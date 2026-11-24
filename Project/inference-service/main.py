"""inference-service: a thin adapter in front of the language model.

The backend is chosen by configuration only (no code change):
- local mode: llama.cpp server running in the cluster
- API mode:   any OpenAI-compatible provider (OpenAI, Mistral, ...)
Both expose the same endpoint: POST {LLM_BASE_URL}/chat/completions.
"""
import os
import time
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configuration (ConfigMap + Secret in Kubernetes)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8080/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-1.5b-instruct")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a customer support assistant. Answer briefly and politely.",
)

BACKEND = urlparse(LLM_BASE_URL).hostname


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One HTTP client for the whole app (reuses connections to the backend)
    headers = {"Authorization": f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {}
    app.state.client = httpx.AsyncClient(base_url=LLM_BASE_URL, headers=headers, timeout=LLM_TIMEOUT)
    yield
    await app.state.client.aclose()


app = FastAPI(title="TokenWise inference-service", lifespan=lifespan)


class GenerateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    max_tokens: int = Field(default=256, ge=1, le=1024)


class GenerateResponse(BaseModel):
    answer: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    backend: str
    model: str


@app.get("/health")
def health():
    # Liveness: the process is up
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    # Readiness: the model backend answers
    try:
        response = await app.state.client.get("/models")
        response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail=f"Backend {BACKEND} not reachable")
    return {"status": "ready", "backend": BACKEND}


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.question},
        ],
        "max_tokens": request.max_tokens,
    }
    start = time.perf_counter()
    try:
        response = await app.state.client.post("/chat/completions", json=payload)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Backend {BACKEND} timed out")
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"Backend {BACKEND} error: {error}")
    latency_ms = int((time.perf_counter() - start) * 1000)

    data = response.json()
    usage = data.get("usage", {})
    return GenerateResponse(
        answer=data["choices"][0]["message"]["content"],
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        latency_ms=latency_ms,
        backend=BACKEND,
        model=LLM_MODEL,
    )
