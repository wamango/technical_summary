import os
import time
import json
import uuid
import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

app = FastAPI(title="OpenAI Proxy for IDEA - Debug V2.3", version="2.3.0")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://10.10.55.244:9997")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-yE7cO7oR9nF2d")

print("🚀 IDEA Debug Proxy V2.3 Started")


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

        # 清理字段
        body.pop("tools", None)
        body.pop("tool_choice", None)
        body.pop("parallel_tool_calls", None)

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
            return data

        # ==================== Streaming Debug ====================
        async def generate_stream() -> AsyncGenerator[str, None]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created = int(time.time())
            token_count = 0
            sent_stop_chunk = False
            sent_done_marker = False

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
                                fallback_chunk = make_stream_chunk(chunk_id, created, model, content=data)
                                yield f"data: {json.dumps(fallback_chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"[{request_id}] Stream proxy error: {e}")
                traceback.print_exc()
                error_chunk = make_stream_chunk(chunk_id, created, model, content=f"Proxy stream error: {e}")
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

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