#!/usr/bin/env python3
"""
IntelliJ IDEA / Koog OpenAI-compatible proxy.

This script fixes errors like:

    Field 'choices' is required for type ... OpenAIChatCompletionStreamResponse

The reason is that IDEA's Koog OpenAI client strictly expects every streaming
SSE JSON message from /v1/chat/completions to be an OpenAI Chat Completions
chunk with a top-level "choices" field. Some providers or adapter scripts emit
Responses API / Claude-style events such as:

    {"type": "response.output_text.delta", "delta": "..."}

Those events are valid upstream, but not valid for Koog. This proxy receives
requests from IDEA, forwards them upstream, and normalizes all streaming events
into OpenAI-compatible chunks before returning them to IDEA.

Run:

    UPSTREAM_API_KEY="sk-..." \
    UPSTREAM_BASE_URL="https://api.openai.com" \
    python3 src/main/java/com/example/demo/main.py

IDEA OpenAI-compatible provider settings:

    Base URL: http://127.0.0.1:8000/v1
    API Key: any value, or PROXY_API_KEY if configured

Environment:

    HOST                         default: 127.0.0.1
    PORT                         default: 8000
    DEFAULT_MODEL                default: gpt-4o-mini
    PROXY_API_KEY                optional incoming key required from IDEA
    UPSTREAM_BASE_URL            default: https://api.openai.com
    UPSTREAM_CHAT_COMPLETIONS_PATH default: /v1/chat/completions
    UPSTREAM_API_KEY             upstream API key
    UPSTREAM_AUTH_HEADER         default: Authorization
    UPSTREAM_AUTH_SCHEME         default: Bearer
    UPSTREAM_TIMEOUT_SECONDS     default: 600
    UPSTREAM_EXTRA_HEADERS       optional JSON object, e.g. '{"X-Foo":"bar"}'
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List, Optional


JsonObject = Dict[str, Any]

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_MODEL = "gpt-4o-mini"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def now_unix() -> int:
    return int(time.time())


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_json_object(raw: bytes, source: str) -> JsonObject:
    try:
        value = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{source} must be a JSON object")
    return value


def upstream_base_url() -> str:
    return env("UPSTREAM_BASE_URL", "https://api.openai.com").rstrip("/")


def upstream_chat_path() -> str:
    path = env("UPSTREAM_CHAT_COMPLETIONS_PATH", "/v1/chat/completions")
    return path if path.startswith("/") else f"/{path}"


def upstream_url(path: str) -> str:
    return f"{upstream_base_url()}{path}"


def extra_upstream_headers() -> Dict[str, str]:
    raw = env("UPSTREAM_EXTRA_HEADERS")
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"UPSTREAM_EXTRA_HEADERS is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("UPSTREAM_EXTRA_HEADERS must be a JSON object")
    return {str(key): str(val) for key, val in value.items()}


def upstream_headers() -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream, application/json",
        "User-Agent": "idea-koog-openai-compat-proxy/1.0",
    }
    headers.update(extra_upstream_headers())

    api_key = env("UPSTREAM_API_KEY")
    if api_key:
        auth_header = env("UPSTREAM_AUTH_HEADER", "Authorization")
        auth_scheme = env("UPSTREAM_AUTH_SCHEME", "Bearer")
        headers[auth_header] = f"{auth_scheme} {api_key}".strip()
    return headers


def completion_id() -> str:
    return f"chatcmpl-proxy-{int(time.time() * 1000)}"


def error_payload(message: str, status: int = 500, err_type: str = "proxy_error") -> JsonObject:
    return {"error": {"message": message, "type": err_type, "code": status}}


def openai_stream_chunk(
    *,
    chunk_id: str,
    model: str,
    delta: Optional[JsonObject] = None,
    finish_reason: Optional[str] = None,
    choices: Optional[List[JsonObject]] = None,
    usage: Optional[JsonObject] = None,
) -> JsonObject:
    payload: JsonObject = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": now_unix(),
        "model": model,
        "choices": choices
        if choices is not None
        else [{"index": 0, "delta": delta or {}, "finish_reason": finish_reason}],
    }
    if usage is not None:
        payload["usage"] = usage
    return payload


def openai_chat_completion(
    *,
    request: JsonObject,
    content: str,
    finish_reason: str = "stop",
    usage: Optional[JsonObject] = None,
) -> JsonObject:
    model = str(request.get("model") or env("DEFAULT_MODEL", DEFAULT_MODEL))
    payload: JsonObject = {
        "id": completion_id(),
        "object": "chat.completion",
        "created": now_unix(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
    }
    if usage is not None:
        payload["usage"] = usage
    return payload


def text_from_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("text") or value.get("content") or value.get("output_text")
        return text if isinstance(text, str) else ""
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            parts.append(text_from_content(item))
        return "".join(parts)
    return str(value)


def text_delta_from_event(event: JsonObject) -> str:
    for key in ("delta", "text", "content", "output_text"):
        value = event.get(key)
        if isinstance(value, str):
            return value

    delta = event.get("delta")
    if isinstance(delta, dict):
        text = delta.get("content") or delta.get("text") or delta.get("output_text")
        if isinstance(text, str):
            return text

    message = event.get("message")
    if isinstance(message, dict):
        return text_from_content(message.get("content"))

    # Common OpenAI Responses API shapes.
    for key in ("item", "content", "output", "response"):
        value = event.get(key)
        if isinstance(value, dict):
            text = value.get("text") or value.get("delta") or value.get("content") or value.get("output_text")
            if isinstance(text, str):
                return text
            nested = text_from_content(value.get("content"))
            if nested:
                return nested
        elif isinstance(value, list):
            text = text_from_content(value)
            if text:
                return text

    return ""


def usage_from_event(event: JsonObject) -> Optional[JsonObject]:
    usage = event.get("usage")
    if isinstance(usage, dict):
        return usage
    response = event.get("response")
    if isinstance(response, dict) and isinstance(response.get("usage"), dict):
        return response["usage"]
    return None


def is_finish_event(event: JsonObject) -> bool:
    event_type = str(event.get("type") or event.get("event") or "").lower()
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
    if event.get("done") is True:
        return True

    choices = event.get("choices")
    if isinstance(choices, list):
        return any(
            isinstance(choice, dict) and choice.get("finish_reason") is not None
            for choice in choices
        )
    return False


def normalize_stream_event(event: JsonObject, *, chunk_id: str, model: str) -> List[JsonObject]:
    """
    Convert one upstream SSE JSON object to zero or more OpenAI-compatible
    Chat Completions chunks. Every returned object has top-level "choices".
    """
    choices = event.get("choices")
    if isinstance(choices, list):
        normalized = dict(event)
        normalized.setdefault("id", chunk_id)
        normalized.setdefault("object", "chat.completion.chunk")
        normalized.setdefault("created", now_unix())
        normalized.setdefault("model", model)
        return [normalized]

    text = text_delta_from_event(event)
    usage = usage_from_event(event)

    if text:
        chunk = openai_stream_chunk(
            chunk_id=chunk_id,
            model=model,
            delta={"content": text},
            finish_reason=None,
        )
        if usage is not None:
            chunk["usage"] = usage
        return [chunk]

    if usage is not None:
        # OpenAI stream_options.include_usage-compatible shape.
        return [openai_stream_chunk(chunk_id=chunk_id, model=model, choices=[], usage=usage)]

    if is_finish_event(event):
        return [openai_stream_chunk(chunk_id=chunk_id, model=model, delta={}, finish_reason="stop")]

    # Metadata events that do not contain assistant text are intentionally ignored.
    return []


def iter_sse_data(response: Any) -> Iterable[str]:
    data_lines: List[str] = []
    while True:
        raw_line = response.readline()
        if raw_line == b"":
            if data_lines:
                yield "\n".join(data_lines)
            return

        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if line == "":
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())


class IdeaCompatHandler(BaseHTTPRequestHandler):
    server_version = "IdeaKoogOpenAICompatProxy/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(
            "[%s] %s - %s\n"
            % (time.strftime("%Y-%m-%d %H:%M:%S"), self.address_string(), fmt % args)
        )

    def do_GET(self) -> None:  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path in {"/health", "/healthz"}:
            self.send_json({"status": "ok"})
            return
        if path == "/v1/models":
            self.handle_models()
            return
        self.send_json(error_payload(f"Not found: {path}", 404, "not_found"), 404)

    def do_POST(self) -> None:  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path != "/v1/chat/completions":
            self.send_json(error_payload(f"Not found: {path}", 404, "not_found"), 404)
            return
        if not self.authorized():
            self.send_json(error_payload("Unauthorized", 401, "unauthorized"), 401)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = parse_json_object(self.rfile.read(length), "request body")
            if request.get("stream") is True:
                self.handle_stream(request)
            else:
                self.handle_non_stream(request)
        except ValueError as exc:
            self.send_json(error_payload(str(exc), 400, "bad_request"), 400)
        except Exception as exc:
            traceback.print_exc()
            self.send_json(error_payload(str(exc), 500), 500)

    def authorized(self) -> bool:
        expected = env("PROXY_API_KEY")
        if not expected:
            return True
        actual = self.headers.get("Authorization", "")
        return actual == expected or actual == f"Bearer {expected}"

    def send_json(self, payload: JsonObject, status: int = 200) -> None:
        body = json_dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def send_sse_headers(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def write_sse(self, payload: Any) -> None:
        data = payload if isinstance(payload, str) else json_dumps(payload)
        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
        self.wfile.flush()

    def build_upstream_request(self, request: JsonObject) -> urllib.request.Request:
        return urllib.request.Request(
            upstream_url(upstream_chat_path()),
            data=json_dumps(request).encode("utf-8"),
            headers=upstream_headers(),
            method="POST",
        )

    def handle_stream(self, request: JsonObject) -> None:
        model = str(request.get("model") or env("DEFAULT_MODEL", DEFAULT_MODEL))
        chunk_id = completion_id()

        try:
            upstream = urllib.request.urlopen(
                self.build_upstream_request(request),
                timeout=float(env("UPSTREAM_TIMEOUT_SECONDS", "600")),
            )
        except urllib.error.HTTPError as exc:
            self.send_upstream_http_error(exc)
            return
        except urllib.error.URLError as exc:
            self.send_json(error_payload(f"Could not connect to upstream: {exc}", 502), 502)
            return

        self.send_sse_headers()
        sent_stop_chunk = False
        sent_done_marker = False
        try:
            for data in iter_sse_data(upstream):
                if data == "[DONE]":
                    if not sent_stop_chunk:
                        self.write_sse(
                            openai_stream_chunk(
                                chunk_id=chunk_id,
                                model=model,
                                delta={},
                                finish_reason="stop",
                            )
                        )
                        sent_stop_chunk = True
                    self.write_sse("[DONE]")
                    sent_done_marker = True
                    break

                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    self.write_sse(
                        openai_stream_chunk(
                            chunk_id=chunk_id,
                            model=model,
                            delta={"content": data},
                            finish_reason=None,
                        )
                    )
                    continue

                if not isinstance(event, dict):
                    continue

                for chunk in normalize_stream_event(event, chunk_id=chunk_id, model=model):
                    if is_finish_event(chunk):
                        sent_stop_chunk = True
                    self.write_sse(chunk)

            if not sent_stop_chunk:
                self.write_sse(openai_stream_chunk(chunk_id=chunk_id, model=model, delta={}, finish_reason="stop"))
            if not sent_done_marker:
                self.write_sse("[DONE]")
        finally:
            try:
                upstream.close()
            except Exception:
                pass

    def handle_non_stream(self, request: JsonObject) -> None:
        try:
            with urllib.request.urlopen(
                self.build_upstream_request(request),
                timeout=float(env("UPSTREAM_TIMEOUT_SECONDS", "600")),
            ) as upstream:
                raw = upstream.read()
        except urllib.error.HTTPError as exc:
            self.send_upstream_http_error(exc)
            return
        except urllib.error.URLError as exc:
            self.send_json(error_payload(f"Could not connect to upstream: {exc}", 502), 502)
            return

        try:
            payload = parse_json_object(raw, "upstream response")
        except ValueError:
            self.send_json(openai_chat_completion(request=request, content=raw.decode("utf-8", errors="replace")))
            return

        if isinstance(payload.get("choices"), list):
            self.send_json(payload)
            return

        content = ""
        if isinstance(payload.get("output_text"), str):
            content = payload["output_text"]
        elif isinstance(payload.get("message"), dict):
            content = text_from_content(payload["message"].get("content"))
        elif isinstance(payload.get("response"), dict):
            content = text_from_content(payload["response"].get("output_text"))
        else:
            content = text_from_content(payload.get("content"))

        self.send_json(openai_chat_completion(request=request, content=content, usage=usage_from_event(payload)))

    def handle_models(self) -> None:
        if not self.authorized():
            self.send_json(error_payload("Unauthorized", 401, "unauthorized"), 401)
            return
        try:
            req = urllib.request.Request(upstream_url("/v1/models"), headers=upstream_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=15) as upstream:
                payload = parse_json_object(upstream.read(), "upstream models response")
            self.send_json(payload)
        except Exception:
            model = env("DEFAULT_MODEL", DEFAULT_MODEL)
            self.send_json(
                {
                    "object": "list",
                    "data": [{"id": model, "object": "model", "created": 0, "owned_by": "proxy"}],
                }
            )

    def send_upstream_http_error(self, exc: urllib.error.HTTPError) -> None:
        status = exc.code or 502
        try:
            raw = exc.read()
            payload = parse_json_object(raw, "upstream error response")
        except Exception:
            text = raw.decode("utf-8", errors="replace") if "raw" in locals() and raw else str(exc)
            payload = error_payload(f"Upstream HTTP {status}: {text}", status, "upstream_error")
        self.send_json(payload, status)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IDEA / Koog OpenAI-compatible proxy")
    parser.add_argument("--host", default=env("HOST", DEFAULT_HOST), help="listen host")
    parser.add_argument("--port", type=int, default=int(env("PORT", str(DEFAULT_PORT))), help="listen port")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), IdeaCompatHandler)
    print(f"IDEA OpenAI compatibility proxy listening on http://{args.host}:{args.port}/v1", file=sys.stderr)
    print(f"Upstream chat endpoint: {upstream_url(upstream_chat_path())}", file=sys.stderr)
    if not env("UPSTREAM_API_KEY"):
        print("Warning: UPSTREAM_API_KEY is not set; upstream may reject requests.", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
