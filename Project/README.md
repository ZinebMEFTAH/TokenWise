# TokenWise

A distributed gateway in front of an LLM for a customer-support platform: it recognises a question already asked in another form (semantic cache) and returns the validated answer without calling the model. Per-team API keys, quotas and usage accounting.

Binôme: Zineb Meftah, Therence Thai. M1 MLSD, Programmation distribuée (Benoît Charroux).

## Layout

| Folder | Content |
|---|---|
| `inference-service/` | FastAPI adapter in front of the model: local llama.cpp or external OpenAI-compatible API |
| `gateway/` | *(to come)* entry point: API keys, quotas, cache then model, usage log |
| `cache-service/` | *(to come)* embeddings + pgvector nearest-neighbour search |
| `k8s/` | Kubernetes and Istio manifests |
| `models/` | GGUF model files, downloaded locally, not committed |
