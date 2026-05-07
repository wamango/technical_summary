import os
import time
import json
import uuid
import traceback
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

app = FastAPI(title="OpenAI Proxy for IDEA - Debug V2.3", version="2.3.0")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://10.10.55.244:9997")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-yE7cO7oR9nF2d")

print("🚀 IDEA Debug Proxy V2.3 Started")


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

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=180.0
            )

        print(f"[{request_id}] Backend status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"[{request_id}] Backend Error Body: {resp.text[:500]}")
            return JSONResponse(status_code=resp.status_code, content={"error": "backend error"})

        if not stream:
            data = resp.json()
            return data

        # ==================== Streaming Debug ====================
        async def generate_stream() -> AsyncGenerator[str, None]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created = int(time.time())
            token_count = 0

            print(f"[{request_id}] === Streaming Started ===")

            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if line == "data: [DONE]" or line.endswith("[DONE]"):
                    print(f"[{request_id}] [DONE] received")
                    yield "data: [DONE]\n\n"
                    continue

                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                        original_chunk = json.dumps(chunk, ensure_ascii=False)[:400]
                        print(f"[{request_id}] Raw chunk: {original_chunk}...")

                        if isinstance(chunk, dict):
                            chunk.setdefault("id", chunk_id)
                            chunk.setdefault("object", "chat.completion.chunk")
                            chunk.setdefault("created", created)
                            chunk.setdefault("model", model)

                            for choice in chunk.get("choices", []):
                                if isinstance(choice, dict):
                                    delta = choice.setdefault("delta", {})
                                    content = delta.get("content") or delta.get("text") or ""
                                    if content:
                                        token_count += 1
                                        print(f"[{request_id}] Token {token_count}: {content}")

                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    except Exception as e:
                        print(f"[{request_id}] Parse error: {e}")
                        yield f"{line}\n\n"

            print(f"[{request_id}] Streaming ended, total tokens: {token_count}")
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