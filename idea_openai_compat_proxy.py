#!/usr/bin/env python3
"""
OpenAI-compatible streaming proxy for IntelliJ IDEA / Koog.

Why this exists
---------------
JetBrains' Koog OpenAI client expects every Server-Sent Events (SSE) JSON
message from /v1/chat/completions?stream=true to match OpenAI's Chat
Completions chunk schema. In particular, each non-[DONE] event must contain a
top-level "choices" field. Some OpenAI-compatible providers, local gateways, or
Responses API adapters emit events such as:

    {"type": "response.output_text.delta", "delta": "..."}

Those events are valid for their own API, but Koog fails with:

    Field 'choices' is required ... OpenAIChatCompletionStreamResponse

This proxy accepts Chat Completions requests from IDEA and normalizes upstream
streaming events so Koog always receives OpenAI-compatible chunks.

Quick start
-----------
1. Start this proxy:

    UPSTREAM_API_KEY="sk-..." \
    UPSTREAM_BASE_URL="https://api.openai.com" \
    python3 idea_openai_compat_proxy.py

2. In IntelliJ IDEA's OpenAI-compatible provider settings:

    Base URL: http://127.0.0.1:8000/v1
    API key:  any value, unless PROXY_API_KEY is configured

Important environment variables
-------------------------------
UPSTREAM_BASE_URL
    Upstream API origin. Default: https://api.openai.com

UPSTREAM_CHAT_COMPLETIONS_PATH
    Upstream chat endpoint path. Default: /v1/chat/completions

UPSTREAM_API_KEY
    API key sent to the upstream provider.

UPSTREAM_AUTH_HEADER
    Header used for upstream auth. Default: Authorization

UPSTREAM_AUTH_SCHEME
    Auth scheme used when UPSTREAM_AUTH_HEADER is Authorization.
    Default: Bearer. Set to an empty string to send the raw key.

PROXY_API_KEY
    Optional API key required from IDEA. If unset, incoming auth is not checked.

DEFAULT_MODEL
    Model returned by /v1/models fallback. Default: gpt-4o-mini

HOST / PORT
    Listen address. Defaults: 127.0.0.1 / 8000

UPSTREAM_EXTRA_HEADERS
    Optional JSON object of extra headers to send upstream.
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
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Iterable, List, Optional, Tuple


JsonObject = Dict[str, Any]


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_MODEL = "gpt-4o-mini"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def now_unix() -> int:
    return int(time.time())


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_json_object(raw: bytes, what: str) -> JsonObject:
    try:
        value = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {what}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{what} must be a JSON object")
    return value


def configured_extra_headers() -> Dict[str, str]:
    raw = env("UPSTREAM_EXTRA_HEADERS")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"UPSTREAM_EXTRA_HEADERS is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("UPSTREAM_EXTRA_HEADERS must be a JSON object")
    return {str(k): str(v) for k, v in parsed.items()}


def upstream_base_url() -> str:
    return env("UPSTREAM_BASE_URL", "https://api.openai.com").rstrip("/")


def upstream_chat_path() -> str:
    path = env("UPSTREAM_CHAT_COMPLETIONS_PATH", "/v1/chat/completions")
    return path if path.startswith("/") else f"/{path}"


def upstream_url(path: str) -> str:
    return f"{upstream_base_url()}{path}"


def upstream_headers() -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream, application/json",
        "User-Agent": "idea-openai-compat-proxy/1.0",
    }
    headers.update(configured_extra_headers())

    api_key = env("UPSTREAM_API_KEY")
    if api_key:
        auth_header = env("UPSTREAM_AUTH_HEADER", "Authorization")
        auth_scheme = env("UPSTREAM_AUTH_SCHEME", "Bearer")
        headers[auth_header] = f"{auth_scheme} {api_key}".strip()
    return headers


def completion_id() -> str:
    return f"chatcmpl-proxy-{int(time.time() * 1000)}"


def openai_chunk(
    *,
    chunk_id: str,
    model: str,
    delta: Optional[JsonObject] = None,
    finish_reason: Optional[str] = None,
    usage: Optional[JsonObject] = None,
    choices: Optional[List[JsonObject]] = None,
) -> JsonObject:
    if choices is None:
        choices = [
            {
                "index": 0,
                "delta": delta or {},
                "finish_reason": finish_reason,
            }
        ]

    chunk: JsonObject = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": now_unix(),
        "model": model,
        "choices": choices,
    }
    if usage is not None:
        chunk["usage"] = usage
    return chunk


def non_stream_completion(
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


def response_error(message: str, status: int = 500, err_type: str = "proxy_error") -> JsonObject:
    return {
        "error": {
            "message": message,
            "type": err_type,
            "code": status,
        }
    }


def extract_text_from_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: List[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    if isinstance(value, dict):
        text = value.get("text") or value.get("content")
        return text if isinstance(text, str) else ""
    return str(value)


def extract_text_delta(event: JsonObject) -> str:
    """Best-effort conversion for common non-OpenAI streaming event shapes."""
    direct_keys = ("delta", "text", "content", "output_text", "message")
    for key in direct_keys:
        value = event.get(key)
        if isinstance(value, str):
            return value

    delta = event.get("delta")
    if isinstance(delta, dict):
        text = delta.get("content") or delta.get("text")
        if isinstance(text, str):
            return text

    message = event.get("message")
    if isinstance(message, dict):
        return extract_text_from_content(message.get("content"))

    # OpenAI Responses API often nests output text under item/content objects.
    for container_key in ("item", "content", "output"):
        container = event.get(container_key)
        if isinstance(container, dict):
            text = (
                container.get("text")
                or container.get("delta")
                or container.get("content")
                or container.get("output_text")
            )
            if isinstance(text, str):
                return text
        elif isinstance(container, list):
            text = extract_text_from_content(container)
            if text:
                return text

    response = event.get("response")
    if isinstance(response, dict):
        text = response.get("output_text")
        if isinstance(text, str):
            return text

    return ""


def extract_usage(event: JsonObject) -> Optional[JsonObject]:
    usage = event.get("usage")
    if isinstance(usage, dict):
        return usage
    response = event.get("response")
    if isinstance(response, dict) and isinstance(response.get("usage"), dict):
        return response["usage"]
    return None


def is_done_event(event: JsonObject) -> bool:
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
    """Return zero or more OpenAI-compatible stream chunks for one upstream event."""
    choices = event.get("choices")
    if isinstance(choices, list):
        # Already Chat Completions shaped. Preserve provider fields, but ensure
        # fields Koog's strict serializer expects are present.
        normalized = dict(event)
        normalized.setdefault("id", chunk_id)
        normalized.setdefault("object", "chat.completion.chunk")
        normalized.setdefault("created", now_unix())
        normalized.setdefault("model", model)
        return [normalized]

    usage = extract_usage(event)
    if usage is not None and not extract_text_delta(event):
        # OpenAI-compatible stream_options.include_usage sends choices: [].
        return [
            openai_chunk(
                chunk_id=chunk_id,
                model=model,
                choices=[],
                usage=usage,
            )
        ]

    text = extract_text_delta(event)
    if text:
        return [
            openai_chunk(
                chunk_id=chunk_id,
                model=model,
                delta={"content": text},
                finish_reason=None,
            )
        ]

    if is_done_event(event):
        return [
            openai_chunk(
                chunk_id=chunk_id,
                model=model,
                delta={},
                finish_reason="stop",
            )
        ]

    # Ignore upstream metadata events that cannot be represented as assistant text.
    return []


def iter_sse_data_lines(response: Any) -> Iterable[str]:
    """Yield complete SSE data payloads from an urllib response."""
    data_lines: List[str] = []
    while True:
        raw_line = response.readline()
        if raw_line == b"":
            if data_lines:
                yield "\n".join(data_lines)
            break

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


class ProxyHandler(BaseHTTPRequestHandler):
    server_version = "IdeaOpenAICompatProxy/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(
            "[%s] %s - %s\n"
            % (time.strftime("%Y-%m-%d %H:%M:%S"), self.address_string(), fmt % args)
        )

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in {"/health", "/healthz"}:
            self.send_json({"status": "ok"})
            return

        if parsed.path == "/v1/models":
            self.handle_models()
            return

        self.send_json(response_error(f"Not found: {parsed.path}", 404), 404)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/v1/chat/completions":
            self.send_json(response_error(f"Not found: {parsed.path}", 404), 404)
            return

        if not self.authorized():
            self.send_json(response_error("Unauthorized", 401, "unauthorized"), 401)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            request_body = self.rfile.read(length)
            request_json = parse_json_object(request_body, "request body")
            if request_json.get("stream") is True:
                self.handle_streaming_chat(request_json)
            else:
                self.handle_non_streaming_chat(request_json)
        except ValueError as exc:
            self.send_json(response_error(str(exc), 400, "bad_request"), 400)
        except Exception as exc:  # Keep IDEA from seeing malformed empty 200s.
            traceback.print_exc()
            self.send_json(response_error(str(exc), 500), 500)

    def authorized(self) -> bool:
        expected = env("PROXY_API_KEY")
        if not expected:
            return True
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {expected}" or header == expected

    def send_json(self, payload: JsonObject, status: int = 200) -> None:
        body = dump_json(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def send_sse_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def write_sse_data(self, payload: Any) -> None:
        if isinstance(payload, str):
            data = payload
        else:
            data = dump_json(payload)
        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
        self.wfile.flush()

    def upstream_request(self, request_json: JsonObject) -> urllib.request.Request:
        body = dump_json(request_json).encode("utf-8")
        return urllib.request.Request(
            upstream_url(upstream_chat_path()),
            data=body,
            headers=upstream_headers(),
            method="POST",
        )

    def handle_streaming_chat(self, request_json: JsonObject) -> None:
        model = str(request_json.get("model") or env("DEFAULT_MODEL", DEFAULT_MODEL))
        chunk_id = completion_id()

        try:
            req = self.upstream_request(request_json)
            timeout = float(env("UPSTREAM_TIMEOUT_SECONDS", "600"))
            upstream = urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            self.send_upstream_http_error(exc)
            return
        except urllib.error.URLError as exc:
            self.send_json(response_error(f"Could not connect to upstream: {exc}", 502), 502)
            return

        self.send_sse_headers()
        sent_stop_chunk = False
        sent_done_marker = False
        try:
            for data in iter_sse_data_lines(upstream):
                if data == "[DONE]":
                    if not sent_stop_chunk:
                        self.write_sse_data(
                            openai_chunk(
                                chunk_id=chunk_id,
                                model=model,
                                delta={},
                                finish_reason="stop",
                            )
                        )
                        sent_stop_chunk = True
                    self.write_sse_data("[DONE]")
                    sent_done_marker = True
                    break

                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    # Raw text is uncommon, but converting it is safer for Koog
                    # than forwarding a non-JSON SSE payload.
                    self.write_sse_data(
                        openai_chunk(
                            chunk_id=chunk_id,
                            model=model,
                            delta={"content": data},
                            finish_reason=None,
                        )
                    )
                    continue

                if not isinstance(event, dict):
                    continue

                normalized_chunks = normalize_stream_event(event, chunk_id=chunk_id, model=model)
                for chunk in normalized_chunks:
                    if is_done_event(chunk):
                        sent_stop_chunk = True
                    self.write_sse_data(chunk)

            if not sent_stop_chunk:
                self.write_sse_data(
                    openai_chunk(
                        chunk_id=chunk_id,
                        model=model,
                        delta={},
                        finish_reason="stop",
                    )
                )
                sent_stop_chunk = True

            if not sent_done_marker:
                self.write_sse_data("[DONE]")
        finally:
            try:
                upstream.close()
            except Exception:
                pass

    def handle_non_streaming_chat(self, request_json: JsonObject) -> None:
        try:
            req = self.upstream_request(request_json)
            timeout = float(env("UPSTREAM_TIMEOUT_SECONDS", "600"))
            with urllib.request.urlopen(req, timeout=timeout) as upstream:
                raw = upstream.read()
        except urllib.error.HTTPError as exc:
            self.send_upstream_http_error(exc)
            return
        except urllib.error.URLError as exc:
            self.send_json(response_error(f"Could not connect to upstream: {exc}", 502), 502)
            return

        try:
            payload = parse_json_object(raw, "upstream response")
        except ValueError:
            self.send_json(non_stream_completion(request=request_json, content=raw.decode("utf-8")))
            return

        if isinstance(payload.get("choices"), list):
            self.send_json(payload)
            return

        content = ""
        if isinstance(payload.get("output_text"), str):
            content = payload["output_text"]
        elif isinstance(payload.get("response"), dict):
            content = extract_text_from_content(payload["response"].get("output_text"))
        elif isinstance(payload.get("message"), dict):
            content = extract_text_from_content(payload["message"].get("content"))
        elif isinstance(payload.get("content"), (str, list, dict)):
            content = extract_text_from_content(payload.get("content"))

        usage = extract_usage(payload)
        self.send_json(non_stream_completion(request=request_json, content=content, usage=usage))

    def handle_models(self) -> None:
        if not self.authorized():
            self.send_json(response_error("Unauthorized", 401, "unauthorized"), 401)
            return

        # Model listing is not critical for IDEA chat. Try upstream first, then
        # return a minimal OpenAI-compatible fallback.
        try:
            req = urllib.request.Request(
                upstream_url("/v1/models"),
                headers=upstream_headers(),
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=15) as upstream:
                raw = upstream.read()
            payload = parse_json_object(raw, "upstream models response")
            self.send_json(payload)
            return
        except Exception:
            model = env("DEFAULT_MODEL", DEFAULT_MODEL)
            self.send_json(
                {
                    "object": "list",
                    "data": [
                        {
                            "id": model,
                            "object": "model",
                            "created": 0,
                            "owned_by": "proxy",
                        }
                    ],
                }
            )

    def send_upstream_http_error(self, exc: urllib.error.HTTPError) -> None:
        status = exc.code or 502
        try:
            raw = exc.read()
        except Exception:
            raw = b""

        try:
            payload = parse_json_object(raw, "upstream error response")
        except ValueError:
            text = raw.decode("utf-8", errors="replace") if raw else str(exc)
            payload = response_error(f"Upstream HTTP {status}: {text}", status, "upstream_error")

        self.send_json(payload, status)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenAI-compatible proxy for IntelliJ IDEA / Koog")
    parser.add_argument("--host", default=env("HOST", DEFAULT_HOST), help="listen host")
    parser.add_argument("--port", type=int, default=int(env("PORT", str(DEFAULT_PORT))), help="listen port")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ProxyHandler)
    print(
        f"IDEA OpenAI compatibility proxy listening on http://{args.host}:{args.port}/v1",
        file=sys.stderr,
    )
    print(f"Upstream: {upstream_url(upstream_chat_path())}", file=sys.stderr)
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
