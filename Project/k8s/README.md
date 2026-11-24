# Kubernetes manifests

Everything runs in the `tokenwise` namespace.

| File | Content |
|---|---|
| `namespace.yaml` | Namespace `tokenwise` |
| `llama-server.yaml` | Local model backend: PVC `models` (2 Gi), Deployment `llama-server` (init container downloads the GGUF model once into the PVC; llama.cpp with `-t 4` = CPU limit), Service port 80 → 8080 |
| `inference-service.yaml` | ConfigMap `inference-config` (backend URL + model), Deployment `inference-service` (2 replicas, liveness `/health`, readiness `/ready`, optional Secret `llm-api-key`), NodePort Service port 80 → 8080 |

## Deploy on minikube

```bash
kubectl apply -f namespace.yaml
kubectl apply -f llama-server.yaml -f inference-service.yaml
kubectl -n tokenwise get pods -w        # first start: ~5 min (model download + llama.cpp image pull)

kubectl -n tokenwise port-forward svc/inference-service 8000:80
curl -s localhost:8000/generate -H 'Content-Type: application/json' -d '{"question":"How do I return a damaged item?"}'
```

## Switch to API mode

```bash
kubectl -n tokenwise create secret generic llm-api-key --from-literal=LLM_API_KEY=<key>
kubectl -n tokenwise patch configmap inference-config --type merge \
  -p '{"data":{"LLM_BASE_URL":"https://api.openai.com/v1","LLM_MODEL":"<model>"}}'
kubectl -n tokenwise rollout restart deploy/inference-service
kubectl -n tokenwise scale deploy/llama-server --replicas=0   # local model no longer needed
```
