# inference-service

FastAPI adapter in front of the language model. The backend is chosen by environment variables only: a local llama.cpp server or any OpenAI-compatible API.

| Method | Path | |
|---|---|---|
| POST | `/generate` | `{"question": "...", "max_tokens": 256}` → `{answer, prompt_tokens, completion_tokens, latency_ms, backend, model}` |
| GET | `/health` | Liveness: the process is up |
| GET | `/ready` | Readiness: the model backend answers (503 otherwise) |

Errors: 422 invalid request, 502 backend error, 504 backend timeout. Swagger: `/docs`.

| Variable | Default | |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:8080/v1` | OpenAI-compatible base URL |
| `LLM_MODEL` | `qwen2.5-1.5b-instruct` | Model name sent to the backend |
| `LLM_API_KEY` | *(empty)* | Only for API mode (K8s Secret) |
| `LLM_TIMEOUT` | `60` | Seconds |
| `SYSTEM_PROMPT` | support assistant prompt | |

## Run locally

```bash
# 1. model backend (llama.cpp + Qwen2.5-1.5B, model file in ../models/)
docker run -d --name llama-server -p 8080:8080 -v "$PWD/../models:/models:ro" \
  ghcr.io/ggml-org/llama.cpp:server -m /models/qwen2.5-1.5b-instruct-q4_k_m.gguf --host 0.0.0.0 --port 8080 -c 4096

# 2. adapter
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --port 8000

curl -s localhost:8000/generate -H 'Content-Type: application/json' -d '{"question":"How can I reset my password?"}'
```

API mode: `LLM_BASE_URL=https://api.openai.com/v1 LLM_MODEL=<model> LLM_API_KEY=<key>`.

## Run with Docker

Image: `ethica79/inference-service:1.0` (python:3.12-slim, non-root user, port 8080).

```bash
docker build -t ethica79/inference-service:1.0 .
# both containers on one network, so the adapter reaches llama.cpp by name
# (inside a container, "localhost" is the container itself)
docker network create tokenwise
docker network connect tokenwise llama-server
docker run -d --name inference-service --network tokenwise -p 8000:8080 \
  -e LLM_BASE_URL=http://llama-server:8080/v1 ethica79/inference-service:1.0
```
