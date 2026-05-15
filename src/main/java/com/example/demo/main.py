import os
import time
import json
import uuid
import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

app = FastAPI(title="OpenAI Proxy for IDEA - Debug V2.4", version="2.4.0")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://10.10.55.244:9997")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-yE7cO7oR9nF2d")

# IDEA 连续对话会不断携带历史消息和代码上下文。这里在代理层做一次保守裁剪，
# 避免本地模型后端报 prompt length > max_model_len。
CONTEXT_TRIM_ENABLED = os.getenv("CONTEXT_TRIM_ENABLED", "true").lower() != "false"
MAX_PROMPT_TOKENS = int(os.getenv("MAX_PROMPT_TOKENS", "9000"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
MAX_SINGLE_MESSAGE_TOKENS = int(os.getenv("MAX_SINGLE_MESSAGE_TOKENS", "3000"))
MAX_SYSTEM_MESSAGE_TOKENS = int(os.getenv("MAX_SYSTEM_MESSAGE_TOKENS", "1800"))
MAX_TOOL_MESSAGE_TOKENS = int(os.getenv("MAX_TOOL_MESSAGE_TOKENS", "4000"))
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "2048"))
TOOL_CALL_MODE = os.getenv("TOOL_CALL_MODE", "prompt").lower()
TOOL_CALL_PARSE_ENABLED = os.getenv("TOOL_CALL_PARSE_ENABLED", "true").lower() != "false"
TOOL_PROMPT_MARKER = "[IDEA_TOOL_CALLS]"

print("🚀 IDEA Debug Proxy V2.4 Started")


def estimate_text_tokens(text: str) -> int:
    """Rough token estimator for mixed code/English/Chinese text."""
    if not text:
        return 0
    ascii_count = sum(1 for char in text if ord(char) < 128)
    non_ascii_count = len(text) - ascii_count
    return max(1, int(ascii_count / 4 + non_ascii_count / 1.5))


def estimate_value_tokens(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return estimate_text_tokens(value)
    return estimate_text_tokens(json.dumps(value, ensure_ascii=False))


def estimate_message_tokens(message: Dict[str, Any]) -> int:
    # ChatML-like overhead. It is approximate, but intentionally conservative.
    return (
        8
        + estimate_value_tokens(message.get("role"))
        + estimate_value_tokens(message.get("name"))
        + estimate_value_tokens(message.get("content"))
    )


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    return 4 + sum(estimate_message_tokens(message) for message in messages)


def trim_text_to_tokens(text: str, max_tokens: int, keep: str = "end") -> str:
    if estimate_text_tokens(text) <= max_tokens:
        return text

    notice = "\n\n[代理提示：前面内容过长，已自动截断以避免超过本地模型上下文。]\n\n"
    if keep == "start":
        notice = "\n\n[代理提示：后面内容过长，已自动截断以避免超过本地模型上下文。]\n\n"

    available_tokens = max_tokens - estimate_text_tokens(notice)
    if available_tokens <= 0:
        return ""

    low, high = 0, len(text)
    best = ""
    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid] if keep == "start" else text[-mid:]
        if estimate_text_tokens(candidate) <= available_tokens:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1

    return f"{best}{notice}" if keep == "start" else f"{notice}{best}"


def trim_message_to_tokens(
    message: Dict[str, Any],
    max_tokens: int,
    keep: str = "end",
) -> Dict[str, Any]:
    trimmed = dict(message)
    content = trimmed.get("content")
    role_overhead = 8 + estimate_value_tokens(trimmed.get("role")) + estimate_value_tokens(trimmed.get("name"))
    content_budget = max(0, max_tokens - role_overhead)

    if isinstance(content, str):
        trimmed["content"] = trim_text_to_tokens(content, content_budget, keep)
    elif content is not None and estimate_value_tokens(content) > content_budget:
        # 本地代码模型一般只需要文本；复杂 content 过长时转成文本再裁剪。
        trimmed["content"] = trim_text_to_tokens(extract_text(content), content_budget, keep)
    return trimmed


def cap_completion_tokens(body: Dict[str, Any], request_id: str) -> None:
    for key in ("max_tokens", "max_completion_tokens"):
        value = body.get(key)
        if isinstance(value, int) and value > MAX_COMPLETION_TOKENS:
            print(f"[{request_id}] Cap {key}: {value} -> {MAX_COMPLETION_TOKENS}")
            body[key] = MAX_COMPLETION_TOKENS


def get_tool_call_mode() -> str:
    if TOOL_CALL_MODE in {"prompt", "pass_through", "drop"}:
        return TOOL_CALL_MODE
    print(f"[proxy] Unknown TOOL_CALL_MODE={TOOL_CALL_MODE!r}, fallback to prompt")
    return "prompt"


def json_dumps_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def tool_choice_is_none(tool_choice: Any) -> bool:
    if tool_choice is None:
        return False
    if isinstance(tool_choice, str):
        return tool_choice.lower() == "none"
    if isinstance(tool_choice, dict):
        choice_type = str(tool_choice.get("type") or "").lower()
        return choice_type == "none"
    return False


def build_tool_prompt(tools: List[Dict[str, Any]], tool_choice: Any) -> str:
    function_tools: List[Dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") != "function":
            continue
        function = tool.get("function")
        if not isinstance(function, dict) or not function.get("name"):
            continue
        function_tools.append(
            {
                "name": function.get("name"),
                "description": function.get("description", ""),
                "parameters": function.get("parameters", {"type": "object", "properties": {}}),
            }
        )

    if not function_tools:
        return ""

    choice_instruction = "Tool use is optional. If no tool is needed, answer normally."
    if isinstance(tool_choice, str) and tool_choice.lower() in {"required", "any"}:
        choice_instruction = "You must call one of the available tools."
    elif isinstance(tool_choice, dict):
        function_choice = tool_choice.get("function")
        if isinstance(function_choice, dict) and function_choice.get("name"):
            choice_instruction = f"You must call the tool named {function_choice['name']!r}."
        elif str(tool_choice.get("type") or "").lower() == "required":
            choice_instruction = "You must call one of the available tools."

    return (
        f"{TOOL_PROMPT_MARKER}\n"
        "The client supports OpenAI tool calls, but this local backend may only understand text.\n"
        "When a tool call is needed, respond with exactly one JSON object and no markdown:\n"
        '{"tool_calls":[{"name":"tool_name","arguments":{"arg":"value"}}]}\n'
        "The arguments object must match the selected tool schema. Do not explain the tool call.\n"
        f"{choice_instruction}\n"
        "Available tools:\n"
        f"{json.dumps(function_tools, ensure_ascii=False, indent=2)}"
    )


def merge_tool_prompt_into_messages(body: Dict[str, Any], prompt: str) -> None:
    messages = body.get("messages")
    if not isinstance(messages, list):
        body["messages"] = [{"role": "system", "content": prompt}]
        return

    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") not in {"system", "developer"}:
            continue

        content = message.get("content")
        content_text = content if isinstance(content, str) else extract_text(content)
        # Put the tool prompt first because system messages are trimmed from the end.
        message["content"] = f"{prompt}\n\n{content_text}" if content_text else prompt
        return

    messages.insert(0, {"role": "system", "content": prompt})


def stringify_tool_calls(tool_calls: Any) -> str:
    if not tool_calls:
        return ""
    try:
        return json.dumps(tool_calls, ensure_ascii=False)
    except TypeError:
        return str(tool_calls)


def downgrade_tool_messages_for_text_backend(body: Dict[str, Any]) -> None:
    messages = body.get("messages")
    if not isinstance(messages, list):
        return

    downgraded_messages: List[Dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue

        normalized = dict(message)
        role = normalized.get("role")

        if role == "tool":
            tool_name = normalized.get("name") or normalized.get("tool_call_id") or "unknown"
            normalized["role"] = "user"
            normalized["content"] = f"[tool result: {tool_name}]\n{extract_text(normalized.get('content'))}"
            normalized.pop("tool_call_id", None)
            normalized.pop("name", None)

        tool_calls = normalized.pop("tool_calls", None)
        if tool_calls:
            content = extract_text(normalized.get("content"))
            call_text = stringify_tool_calls(tool_calls)
            normalized["content"] = (
                f"{content}\n[assistant tool_calls]\n{call_text}" if content else f"[assistant tool_calls]\n{call_text}"
            )

        normalized.pop("function_call", None)
        downgraded_messages.append(normalized)

    body["messages"] = downgraded_messages


def prepare_tools_for_backend(body: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    tools = body.get("tools")
    tool_choice = body.get("tool_choice")
    mode = get_tool_call_mode()
    context = {
        "mode": mode,
        "prompt_tools": False,
        "tools": tools if isinstance(tools, list) else [],
        "tool_choice": tool_choice,
    }

    if not isinstance(tools, list) or not tools:
        return context

    if mode == "pass_through":
        print(f"[{request_id}] Tools pass-through enabled: {len(tools)} tool(s)")
        return context

    body.pop("tools", None)
    body.pop("tool_choice", None)
    body.pop("parallel_tool_calls", None)

    if mode == "drop" or tool_choice_is_none(tool_choice):
        print(f"[{request_id}] Tools removed: mode={mode}, tool_choice={tool_choice}")
        downgrade_tool_messages_for_text_backend(body)
        return context

    prompt = build_tool_prompt(tools, tool_choice)
    if not prompt:
        print(f"[{request_id}] No supported function tools found; tools removed")
        downgrade_tool_messages_for_text_backend(body)
        return context

    merge_tool_prompt_into_messages(body, prompt)
    downgrade_tool_messages_for_text_backend(body)
    context["prompt_tools"] = True
    print(f"[{request_id}] Tools converted to prompt: {len(tools)} tool(s)")
    return context


def get_system_message_budget(message: Dict[str, Any]) -> int:
    content = message.get("content")
    if isinstance(content, str) and TOOL_PROMPT_MARKER in content:
        return max(MAX_SYSTEM_MESSAGE_TOKENS, MAX_TOOL_MESSAGE_TOKENS)
    return MAX_SYSTEM_MESSAGE_TOKENS


def trim_messages_for_local_model(body: Dict[str, Any], request_id: str) -> None:
    if not CONTEXT_TRIM_ENABLED:
        return

    messages = body.get("messages")
    if not isinstance(messages, list):
        return

    normalized_messages = [message for message in messages if isinstance(message, dict)]
    if not normalized_messages:
        return

    original_count = len(normalized_messages)
    original_tokens = estimate_messages_tokens(normalized_messages)

    system_messages = [
        trim_message_to_tokens(message, get_system_message_budget(message), keep="start")
        for message in normalized_messages
        if message.get("role") in {"system", "developer"}
    ][:1]

    conversation_messages = [
        trim_message_to_tokens(message, MAX_SINGLE_MESSAGE_TOKENS, keep="end")
        for message in normalized_messages
        if message.get("role") not in {"system", "developer"}
    ]

    if MAX_HISTORY_MESSAGES > 0 and len(conversation_messages) > MAX_HISTORY_MESSAGES:
        dropped = len(conversation_messages) - MAX_HISTORY_MESSAGES
        print(f"[{request_id}] Drop old history messages: {dropped}")
        conversation_messages = conversation_messages[-MAX_HISTORY_MESSAGES:]

    planned_messages = system_messages + conversation_messages
    while estimate_messages_tokens(planned_messages) > MAX_PROMPT_TOKENS and len(conversation_messages) > 1:
        dropped_message = conversation_messages.pop(0)
        print(
            f"[{request_id}] Drop oldest message to fit context: "
            f"role={dropped_message.get('role')}"
        )
        planned_messages = system_messages + conversation_messages

    if estimate_messages_tokens(planned_messages) > MAX_PROMPT_TOKENS and conversation_messages:
        prefix_messages = system_messages + conversation_messages[:-1]
        latest_budget = MAX_PROMPT_TOKENS - estimate_messages_tokens(prefix_messages) - 16
        latest_budget = max(256, latest_budget)
        conversation_messages[-1] = trim_message_to_tokens(conversation_messages[-1], latest_budget, keep="end")
        planned_messages = system_messages + conversation_messages

    if estimate_messages_tokens(planned_messages) > MAX_PROMPT_TOKENS and system_messages:
        conversation_tokens = estimate_messages_tokens(conversation_messages)
        system_budget = MAX_PROMPT_TOKENS - conversation_tokens - 16
        system_budget = max(128, system_budget)
        system_messages[0] = trim_message_to_tokens(system_messages[0], system_budget, keep="start")
        planned_messages = system_messages + conversation_messages

    trimmed_tokens = estimate_messages_tokens(planned_messages)
    if original_count != len(planned_messages) or original_tokens != trimmed_tokens:
        print(
            f"[{request_id}] Context trim: messages {original_count}->{len(planned_messages)}, "
            f"estimated tokens {original_tokens}->{trimmed_tokens}, limit={MAX_PROMPT_TOKENS}"
        )

    body["messages"] = planned_messages


def make_stream_chunk(
    chunk_id: str,
    created: int,
    model: str,
    content: str = "",
    finish_reason: Optional[str] = None,
    choices: Optional[List[Dict[str, Any]]] = None,
    usage: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a Koog/OpenAI-compatible chat.completion.chunk."""
    chunk: Dict[str, Any] = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": choices
        if choices is not None
        else [
            {
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason,
            }
        ],
    }
    if usage is not None:
        chunk["usage"] = usage
    return chunk


def extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("content") or value.get("text") or value.get("delta") or value.get("output_text")
        return text if isinstance(text, str) else ""
    if isinstance(value, list):
        return "".join(extract_text(item) for item in value)
    return ""


def extract_text_delta(chunk: Dict[str, Any]) -> str:
    """Extract text from common non-OpenAI streaming formats."""
    for key in ("content", "text", "delta", "output_text"):
        value = chunk.get(key)
        if isinstance(value, str):
            return value

    delta = chunk.get("delta")
    if isinstance(delta, dict):
        text = delta.get("content") or delta.get("text") or delta.get("output_text")
        if isinstance(text, str):
            return text

    message = chunk.get("message")
    if isinstance(message, dict):
        return extract_text(message.get("content"))

    # Compatible with OpenAI Responses API style events:
    # {"type":"response.output_text.delta","delta":"..."}
    # {"type":"response.output_item.done","item":{...}}
    for key in ("item", "output", "response"):
        value = chunk.get(key)
        if isinstance(value, dict):
            text = extract_text(value.get("content")) or extract_text(value)
            if text:
                return text
        elif isinstance(value, list):
            text = extract_text(value)
            if text:
                return text

    return ""


def extract_usage(chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    usage = chunk.get("usage")
    if isinstance(usage, dict):
        return usage
    response = chunk.get("response")
    if isinstance(response, dict) and isinstance(response.get("usage"), dict):
        return response["usage"]
    return None


def normalize_tool_arguments(arguments: Any) -> str:
    if arguments is None:
        return "{}"
    if isinstance(arguments, str):
        stripped = arguments.strip()
        if not stripped:
            return "{}"
        try:
            return json_dumps_compact(json.loads(stripped))
        except Exception:
            return stripped
    return json_dumps_compact(arguments)


def make_tool_call(name: str, arguments: Any, call_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": call_id or f"call_{uuid.uuid4().hex[:24]}",
        "type": "function",
        "function": {
            "name": name,
            "arguments": normalize_tool_arguments(arguments),
        },
    }


def first_present(mapping: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def normalize_tool_call_item(item: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None

    function = item.get("function")
    name = first_present(item, ["name", "tool_name", "tool", "function_name"])
    arguments = first_present(item, ["arguments", "args", "parameters", "input"], {})

    if isinstance(function, dict):
        name = function.get("name") or name
        arguments = first_present(function, ["arguments", "args", "parameters", "input"], arguments)

    if not isinstance(name, str) or not name:
        return None

    call_id = item.get("id")
    return make_tool_call(name, arguments, call_id if isinstance(call_id, str) else None)


def extract_tool_calls_from_object(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        calls = []
        for item in value:
            call = normalize_tool_call_item(item)
            if call:
                calls.append(call)
        return calls

    if not isinstance(value, dict):
        return []

    for key in ("tool_calls", "toolCalls", "calls"):
        calls_value = value.get(key)
        if isinstance(calls_value, list):
            calls = extract_tool_calls_from_object(calls_value)
            if calls:
                return calls

    for key in ("tool_call", "toolCall", "function_call", "functionCall"):
        call_value = value.get(key)
        if isinstance(call_value, dict):
            call = normalize_tool_call_item(call_value)
            if call:
                return [call]

    call = normalize_tool_call_item(value)
    return [call] if call else []


def strip_json_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines:
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def iter_balanced_json_candidates(text: str) -> List[str]:
    candidates: List[str] = []
    for start_index, char in enumerate(text):
        if char not in "{[":
            continue

        stack: List[str] = []
        in_string = False
        escaped = False

        for index in range(start_index, len(text)):
            current = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue

            if current == '"':
                in_string = True
            elif current in "{[":
                stack.append(current)
            elif current in "}]":
                if not stack:
                    break
                opener = stack.pop()
                if (opener == "{" and current != "}") or (opener == "[" and current != "]"):
                    break
                if not stack:
                    candidates.append(text[start_index : index + 1])
                    break

    return candidates


def parse_tool_calls_from_text(text: str) -> List[Dict[str, Any]]:
    if not TOOL_CALL_PARSE_ENABLED:
        return []

    stripped = strip_json_code_fence(text)
    candidates = [stripped] + iter_balanced_json_candidates(stripped)
    seen = set()

    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            value = json.loads(candidate)
        except Exception:
            continue

        calls = extract_tool_calls_from_object(value)
        if calls:
            return calls

    return []


def normalize_non_stream_tool_response(
    data: Dict[str, Any],
    tool_context: Dict[str, Any],
    request_id: str,
) -> Dict[str, Any]:
    if not tool_context.get("prompt_tools"):
        return data

    choices = data.get("choices")
    if not isinstance(choices, list):
        return data

    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            message = {"role": "assistant", "content": choice.get("text", "")}

        if message.get("tool_calls"):
            choice["message"] = message
            choice["finish_reason"] = "tool_calls"
            continue

        content = extract_text(message.get("content")) or extract_text(choice.get("text"))
        calls = parse_tool_calls_from_text(content)
        if not calls:
            continue

        message["role"] = message.get("role") or "assistant"
        message["content"] = None
        message["tool_calls"] = calls
        message.pop("function_call", None)
        choice["message"] = message
        choice["finish_reason"] = "tool_calls"
        print(f"[{request_id}] Parsed {len(calls)} tool call(s) from non-stream response")

    return data


def extract_choice_content(chunk: Dict[str, Any]) -> str:
    choices = chunk.get("choices")
    if not isinstance(choices, list):
        return ""

    parts: List[str] = []
    for choice in choices:
        if not isinstance(choice, dict):
            continue

        delta = choice.get("delta")
        if isinstance(delta, dict):
            text = delta.get("content") or delta.get("text")
            if isinstance(text, str):
                parts.append(text)

        message = choice.get("message")
        if isinstance(message, dict):
            text = extract_text(message.get("content"))
            if text:
                parts.append(text)

        text = choice.get("text")
        if isinstance(text, str):
            parts.append(text)

    return "".join(parts)


def make_tool_call_stream_chunk(
    chunk_id: str,
    created: int,
    model: str,
    tool_calls: List[Dict[str, Any]],
) -> Dict[str, Any]:
    delta_tool_calls = []
    for index, call in enumerate(tool_calls):
        delta_tool_calls.append(
            {
                "index": index,
                "id": call["id"],
                "type": "function",
                "function": call["function"],
            }
        )

    return {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"tool_calls": delta_tool_calls},
                "finish_reason": None,
            }
        ],
    }


def make_tool_call_finish_chunk(chunk_id: str, created: int, model: str) -> Dict[str, Any]:
    return {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "tool_calls",
            }
        ],
    }


def is_finish_chunk(chunk: Dict[str, Any]) -> bool:
    event_type = str(chunk.get("type") or chunk.get("event") or "").lower()
    if event_type in {
        "done",
        "message_stop",
        "response.completed",
        "response.done",
        "completion.done",
        "thread.message.completed",
        "run.completed",
    }:
        return True
    if chunk.get("done") is True:
        return True

    choices = chunk.get("choices")
    if isinstance(choices, list):
        return any(
            isinstance(choice, dict) and choice.get("finish_reason") is not None
            for choice in choices
        )
    return False


def normalize_stream_chunk(
    chunk: Dict[str, Any],
    chunk_id: str,
    created: int,
    model: str,
) -> List[Dict[str, Any]]:
    """
    IDEA/Koog requires every streamed JSON object to include top-level choices.
    This function keeps real OpenAI chunks, and converts local-model adapter
    chunks that only have delta/text/content into Chat Completions chunks.
    """
    choices = chunk.get("choices")
    if isinstance(choices, list):
        chunk.setdefault("id", chunk_id)
        chunk.setdefault("object", "chat.completion.chunk")
        chunk.setdefault("created", created)
        chunk.setdefault("model", model)
        return [chunk]

    text = extract_text_delta(chunk)
    usage = extract_usage(chunk)
    if text:
        normalized = make_stream_chunk(chunk_id, created, model, content=text)
        if usage is not None:
            normalized["usage"] = usage
        return [normalized]

    if usage is not None:
        return [make_stream_chunk(chunk_id, created, model, choices=[], usage=usage)]

    if is_finish_chunk(chunk):
        return [make_stream_chunk(chunk_id, created, model, finish_reason="stop")]

    # Ignore metadata events that have no assistant text.
    return []


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    request_id = str(uuid.uuid4())[:8]
    try:
        body = await request.json()
        stream = body.get("stream", False)
        model = body.get("model", "qwen2.5-coder-32B-instruct")
        
        print(f"[{request_id}] Request | Stream: {stream} | Model: {model}")

        # 本地模型不一定原生支持 OpenAI tools；默认转成提示词并在响应侧还原 tool_calls。
        tool_context = prepare_tools_for_backend(body, request_id)
        trim_messages_for_local_model(body, request_id)
        cap_completion_tokens(body, request_id)

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        backend_url = f"{OPENAI_BASE_URL.rstrip('/')}/v1/chat/completions"

        if not stream:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(
                    backend_url,
                    headers=headers,
                    json=body,
                    timeout=180.0
                )

            print(f"[{request_id}] Backend status: {resp.status_code}")

            if resp.status_code != 200:
                print(f"[{request_id}] Backend Error Body: {resp.text[:500]}")
                return JSONResponse(status_code=resp.status_code, content={"error": "backend error"})

            data = resp.json()
            return normalize_non_stream_tool_response(data, tool_context, request_id)

        # ==================== Streaming Debug ====================
        async def generate_stream() -> AsyncGenerator[str, None]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created = int(time.time())
            token_count = 0
            sent_stop_chunk = False
            sent_done_marker = False
            buffered_tool_text: List[str] = []
            buffered_usage: Optional[Dict[str, Any]] = None

            print(f"[{request_id}] === Streaming Started ===")

            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "POST",
                        backend_url,
                        headers=headers,
                        json=body,
                        timeout=180.0,
                    ) as resp:
                        print(f"[{request_id}] Backend status: {resp.status_code}")

                        if resp.status_code != 200:
                            error_body = await resp.aread()
                            error_text = error_body.decode("utf-8", errors="ignore")[:500]
                            print(f"[{request_id}] Backend Error Body: {error_text}")
                            error_chunk = make_stream_chunk(
                                chunk_id,
                                created,
                                model,
                                content=f"Backend error {resp.status_code}: {error_text}",
                            )
                            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                            yield f"data: {json.dumps(make_stream_chunk(chunk_id, created, model, finish_reason='stop'), ensure_ascii=False)}\n\n"
                            yield "data: [DONE]\n\n"
                            return

                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if not line:
                                continue

                            if line == "data: [DONE]" or line.endswith("[DONE]"):
                                print(f"[{request_id}] [DONE] received")
                                if tool_context.get("prompt_tools"):
                                    break
                                if not sent_stop_chunk:
                                    done_chunk = make_stream_chunk(chunk_id, created, model, finish_reason="stop")
                                    yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
                                    sent_stop_chunk = True
                                yield "data: [DONE]\n\n"
                                sent_done_marker = True
                                break

                            data = line[6:].strip() if line.startswith("data:") else line

                            try:
                                chunk = json.loads(data)
                                original_chunk = json.dumps(chunk, ensure_ascii=False)[:400]
                                print(f"[{request_id}] Raw chunk: {original_chunk}...")

                                if not isinstance(chunk, dict):
                                    continue

                                for normalized_chunk in normalize_stream_chunk(chunk, chunk_id, created, model):
                                    if tool_context.get("prompt_tools"):
                                        content = extract_choice_content(normalized_chunk)
                                        if content:
                                            buffered_tool_text.append(content)
                                            token_count += 1
                                            print(f"[{request_id}] Buffered tool token {token_count}: {content}")
                                        usage = extract_usage(normalized_chunk)
                                        if usage is not None:
                                            buffered_usage = usage
                                        continue

                                    if is_finish_chunk(normalized_chunk):
                                        sent_stop_chunk = True

                                    for choice in normalized_chunk.get("choices", []):
                                        if isinstance(choice, dict):
                                            delta = choice.setdefault("delta", {})
                                            content = delta.get("content") or delta.get("text") or ""
                                            if content:
                                                token_count += 1
                                                print(f"[{request_id}] Token {token_count}: {content}")

                                    yield f"data: {json.dumps(normalized_chunk, ensure_ascii=False)}\n\n"
                            except Exception as e:
                                print(f"[{request_id}] Parse error: {e}")
                                if tool_context.get("prompt_tools"):
                                    buffered_tool_text.append(data)
                                    continue
                                fallback_chunk = make_stream_chunk(chunk_id, created, model, content=data)
                                yield f"data: {json.dumps(fallback_chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"[{request_id}] Stream proxy error: {e}")
                traceback.print_exc()
                error_chunk = make_stream_chunk(chunk_id, created, model, content=f"Proxy stream error: {e}")
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

            if tool_context.get("prompt_tools"):
                buffered_text = "".join(buffered_tool_text).strip()
                tool_calls = parse_tool_calls_from_text(buffered_text)
                if tool_calls:
                    print(f"[{request_id}] Parsed {len(tool_calls)} tool call(s) from stream response")
                    tool_chunk = make_tool_call_stream_chunk(chunk_id, created, model, tool_calls)
                    yield f"data: {json.dumps(tool_chunk, ensure_ascii=False)}\n\n"
                    finish_chunk = make_tool_call_finish_chunk(chunk_id, created, model)
                    if buffered_usage is not None:
                        finish_chunk["usage"] = buffered_usage
                    yield f"data: {json.dumps(finish_chunk, ensure_ascii=False)}\n\n"
                else:
                    if buffered_text:
                        fallback_chunk = make_stream_chunk(chunk_id, created, model, content=buffered_text)
                        if buffered_usage is not None:
                            fallback_chunk["usage"] = buffered_usage
                        yield f"data: {json.dumps(fallback_chunk, ensure_ascii=False)}\n\n"
                    done_chunk = make_stream_chunk(chunk_id, created, model, finish_reason="stop")
                    yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
                sent_stop_chunk = True

            print(f"[{request_id}] Streaming ended, total tokens: {token_count}")
            if not sent_stop_chunk:
                done_chunk = make_stream_chunk(chunk_id, created, model, finish_reason="stop")
                yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
            if not sent_done_marker:
                yield "data: [DONE]\n\n"

        return StreamingResponse(generate_stream(), media_type="text/event-stream")

    except Exception as e:
        print(f"[{request_id}] Proxy Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": "qwen2.5-coder-32B-instruct", "object": "model"}]}


@app.get("/")
async def root():
    return {"status": "running"}
