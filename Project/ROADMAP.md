# TokenWise: Distributed Programming project (roadmap)

> A distributed gateway in front of an LLM: it recognises a question already asked in another form (semantic cache) and returns the stored answer without calling the model; it also handles per-team API keys, quotas and usage accounting.
>
> Proposal: [docs/proposition_projet.pdf](docs/proposition_projet.pdf) (v4, 24/11/2026: support use case + pluggable model backend). Brief and slides: teacher's documents (not in the repo). Teacher: Benoît Charroux.
> Tick boxes as work gets done, and log progress at the bottom.

## Deliverables

- Code on **one GitHub repo for the binôme** (with Zineb Meftah): https://github.com/ZinebMEFTAH/TokenWise
- **Mini report** with screenshots + **individual Google Labs screenshots** for each member
- Emailed to benoit.charroux@gmail.com
- **Deadline: 31 January 2027.** About 11 weeks from 12/11, including the holidays, so the 8-week plan fits but leaves little slack for the bonuses.
- Grading priority: number of integrated technologies > code > features > presentation

## Status

**Subject chosen: TokenWise** (proposal v4, Nov 2026). All project code is in this `Project/` folder (per-member folders `Zineb/`, `Therence/` are for individual work). Done so far: `inference-service` (FastAPI adapter + Docker image). 

## Use case: customer support platform

The gateway is shown in front of a **customer support** service, where the same questions come back all the time in different wordings: that is where a semantic cache really pays off. The support context is only the use case, the dataset and the demo; we do **not** build a full ticketing platform.

- **Dataset with intent labels** (Banking77: ~13k banking questions / 77 intents, or Bitext Customer Support: e-commerce, intents). Ground truth for the cache: a cached answer is **correct if the original question has the same intent**.
- **Cache warm-up** from the existing FAQ: the cache is useful from day 1.
- **Only validated answers enter the cache**: a generated answer is cached after a support agent approves it (or a 👍), so a hallucinated answer is never replayed.
- **Minimal frontend**: customer chat widget + admin page (cache hit rate, cost per team, answers waiting for validation). Counts only for presentation: keep it small.

## Architecture (from the proposal)

```
App ──► Istio Gateway ──► gateway (FastAPI: API key, quota, usage log)
                              │ 1. seen before? (REST, then gRPC)
                              ├──► cache-service (FastAPI + fastembed ONNX) ──► PostgreSQL + pgvector
                              │ 2. otherwise
                              └──► inference-service (FastAPI adapter) ──► llama.cpp in-cluster (Qwen2.5-1.5B Q4)
                                                                    or external OpenAI-compatible API
        all inside Kubernetes (minikube), Istio mesh, mTLS STRICT
```

| Component | Tech |
|---|---|
| `gateway` | FastAPI, gRPC client |
| `cache-service` | FastAPI, gRPC server, fastembed (multilingual embeddings, ONNX) |
| `inference-service` | FastAPI adapter, **pluggable backend** chosen by ConfigMap (URL + model) + Secret (API key): local llama.cpp server (Qwen2.5-1.5B-Instruct Q4, draft 0.5B) or external OpenAI-compatible API (OpenAI, Mistral…) |
| Database | PostgreSQL 16 + pgvector, StatefulSet + PVC, ConfigMap + Secret |
| Mesh | Istio Gateway, VirtualService, DestinationRule, PeerAuthentication, AuthorizationPolicy |

Split: **AI part** (cache-service, embeddings, threshold eval, inference, speculative decoding) / **platform part** (gateway, K8s, Istio, RBAC, CI, Terraform). Each reviews the other's code.
- [ ] Decide who takes which part

---

## Step 0: Kick-off

- [x] Environment: Docker Desktop, minikube, kubectl, Istio 1.31.1 (demo profile), Docker Hub `ethica79`
- [x] Subject chosen + proposal written (v3)
- [ ] Proposal sent to / validated by the teacher
- [ ] Choose support domain + dataset (Banking77 = banking, Bitext = e-commerce)
- [ ] Choose demo language (datasets are in English → English demo is simplest; French = translate part of the dataset)
- [x] Shared GitHub repo created: https://github.com/ZinebMEFTAH/TokenWise (branch `main`)
- [ ] Both members can push to it
- [ ] Agree with Zineb on one Docker Hub namespace for the project (`ethica79` used for now, Zineb has `zineb36`)
- [x] Project layout in `Project/`: `inference-service/`, `k8s/`, `models/` (git-ignored), README, .gitignore
- [ ] Rest of layout as services arrive: `gateway/`, `cache-service/`, `docker-compose.yml`, `.github/workflows/` (repo root)

## Weeks 1–2: inference-service on Kubernetes (→ 10/20)

- [x] llama.cpp server running locally with Qwen2.5-1.5B Q4 (check RAM usage): ~1.8 GB RAM with 4k context, ~46 tokens/s generation, 1–2 s per support answer (Docker image `ghcr.io/ggml-org/llama.cpp:server`, 1.16 GB)
- [x] `inference-service` FastAPI adapter: one OpenAI-compatible client (httpx), backend URL/model/key from env; `POST /generate`, `/health`, `/ready`, 502/504 on backend errors (ConfigMap/Secret wiring comes with the K8s step)
- [ ] Both modes work: local llama.cpp and external API
- [x] Dockerfile for the adapter (python:3.12-slim, non-root `appuser`, port 8080, .dockerignore); image `ethica79/inference-service:1.0` (217 MB) built and tested on a Docker network with llama-server (model stays mounted, not in the image)
- [x] Image pushed to Docker Hub: `ethica79/inference-service:1.0` (public)
- [ ] Deployment (liveness/readiness on `/health`) + Service (port 80 → 8080) on minikube
- [ ] Screenshots

## Weeks 3–4: gateway + cache-service + database (→ 14/20, 16/20)

- [ ] `gateway` (FastAPI): `POST /ask`, forwards to inference-service; Swagger on `/docs`
- [ ] `cache-service` (FastAPI): embed question with fastembed, nearest-neighbour search, store new answers
- [ ] PostgreSQL + pgvector: cache table (vector, answer, team, TTL, `validated` flag) + usage table
- [ ] Cache warm-up script: load the FAQ (question/answer pairs) into the cache
- [ ] `docker-compose.yml` for local dev (all services + db)
- [ ] K8s: Deployment + Service per service; PostgreSQL StatefulSet + PVC + ConfigMap + Secret
- [ ] Gateway ↔ cache ↔ inference works end to end in minikube (**second service linked = 14/20**, **database = 16/20**)

## Weeks 5–6: Istio, quotas, CI (→ 12/20 gateway requirement + extras)

- [ ] Istio `Gateway` (`microservice-gateway`) + one `VirtualService` per service, with timeouts and retries
- [ ] API keys per team + daily quota (request refused when over quota)
- [ ] Usage log: team, cache hit/miss, tokens, latency
- [ ] Answer validation: generated answers stored as "pending"; endpoint for an agent to approve/reject (or 👍 feedback); only approved answers are served from the cache
- [ ] GitHub Actions: pytest → build → Trivy scan (fail on critical) → push to Docker Hub

## Weeks 7–8: Security + resilience (→ 18/20)

- [ ] `PeerAuthentication` mTLS STRICT (shown in Kiali)
- [ ] `AuthorizationPolicy`: only the gateway may call cache and inference (403 screenshot)
- [ ] RBAC: one ServiceAccount per service, minimal rights; read-only "developer" role shown with `kubectl auth can-i`
- [ ] NetworkPolicies: only gateway + cache reach the DB (minikube `--cni=calico`)
- [ ] Secrets only in K8s Secrets; non-root slim images
- [ ] `DestinationRule` circuit breaker (outlierDetection) in front of inference-service
- [ ] API mode: Istio outbound `REGISTRY_ONLY` + `ServiceEntry` for the API provider only

## End: bonuses (→ 20/20 and extra points)

- [ ] **gRPC** gateway → cache-service, latency compared with REST
- [ ] **Similarity threshold** chosen on the support dataset (Banking77 / Bitext intents): cache hit correct if same intent → precision / hit-rate curve vs threshold
- [ ] **Speculative decoding** (local mode only): llama.cpp `--model-draft` with 0.5B; tokens/s, acceptance rate, effect of k
- [ ] Observability: Kiali, Prometheus + Grafana (cache hit rate, latency, per team), Jaeger trace
- [ ] HorizontalPodAutoscaler on inference-service
- [ ] **Cloud**: GKE + Terraform (`terraform apply` recreates the cluster)
- [ ] *(optional)* Kafka/Redpanda events + nightly stats CronJob

## Demo + report

- [ ] Minimal frontend: support chat widget + admin page (hit rate, cost per team, pending answers)
- [ ] Locust load test (~1000 questions drawn from the support dataset, several teams, paraphrases of the same intents)
- [ ] Measured: cost avoided in € (API mode), % served by cache, latency cached vs generated, per-team usage, over-quota refusal
- [ ] Resilience demo: delete an inference pod during the test, count failed requests
- [ ] Security screenshots: Kiali mTLS, 403 from AuthorizationPolicy, RBAC refusal, Trivy report
- [ ] Individual Google Labs screenshots (both members)
- [ ] Mini report written, email sent with repo link

---

## Log

| Date | Progress |
|---|---|
| 2026-10-14 | First attempt (Java/Spring "ticketing"): steps 1–4 done, then abandoned. |
| 2026-10-15 | Restart: new binôme, Python + FastAPI. |
| 2026-11-12 | Subject chosen: **TokenWise** (proposal v2 with Zineb Meftah). Roadmap rebuilt from the proposal. Next: validate proposal, create repo, start inference-service. |
| 2026-11-12 | Deadline confirmed: **31/01/2027**. |
| 2026-11-12 | Proposal v2 PDF reviewed and rebuilt (Istio instead of Linkerd, prof's K8s conventions, gRPC, PAWS-X threshold). LaTeX source deleted on request: the PDF can no longer be recompiled. Next: send proposal to teacher, create shared repo. |
| 2026-11-24 | Feasibility review (overall 7/10: strong fit with grading and AI CV, weak point = time with 68 days left and other projects). Use case decided: **customer support platform**. Threshold eval moved from PAWS-X to an intent-labelled support dataset (Banking77 / Bitext); added cache warm-up from FAQ, answer validation before caching, minimal chat + admin frontend. Next: pick domain/dataset + language with Zineb, send proposal, create repo. |
| 2026-11-24 | Proposal updated to **v3** (`proposition_projet.pdf`): customer-support use case, cache warm-up, validated answers, minimal frontend, threshold on Banking77 / Bitext instead of PAWS-X, GitHub link. Shared repo exists: github.com/ZinebMEFTAH/TokenWise. Next: check both can push, pick dataset + language, send proposal. |
| 2026-11-24 | Proposal v3: added Therence Thai as second member. Discussed replacing local llama.cpp with an external API (open question, see proposal: pluggable OpenAI-compatible backend recommended). |
| 2026-11-24 | Decided: **pluggable model backend** (inference-service = FastAPI adapter, local llama.cpp or external OpenAI-compatible API via ConfigMap/Secret; Istio ServiceEntry + REGISTRY_ONLY for egress). Proposal updated to **v4**. |
| 2026-11-24 | Step 1 started. Repo cloned locally. Step 1a: `Project/` layout + README + .gitignore (models excluded), not committed yet. Next 1b: run llama.cpp + Qwen2.5-1.5B locally, measure RAM / tokens/s. |
| 2026-11-24 | Step 1a committed (`9119ef8`, not pushed). Step 1b done: model `qwen2.5-1.5b-instruct-q4_k_m.gguf` (1.1 GB) in `Project/models/`, llama.cpp server container `llama-server` on :8080, OpenAI-compatible `/v1/chat/completions` works; 1.8 GB RAM, ~46 tok/s, 0.8–2 s per answer → local mode is viable. Next 1c: FastAPI adapter `inference-service`. |
| 2026-11-24 | Step 1c done: `Project/inference-service/` (main.py, requirements.txt, README). Tested against local llama-server: generate OK (~0.6 s), 422 on empty question, 503 /ready + 502 /generate when backend stopped, Swagger on /docs. Committed `df5894a` (layout `9119ef8` already pushed). API mode not tested (no key). Next 1d: Dockerfile + push to Docker Hub. |
| 2026-11-24 | Step 1d: Dockerfile + .dockerignore, image `ethica79/inference-service:1.0` built and tested (adapter + llama-server on Docker network `tokenwise`, called by name; /ready 503 with default localhost shows liveness vs readiness). Not committed, not pushed yet. Idea: move GitHub Actions (build + push to Docker Hub) right after step 1e so both members get images automatically. Next: user pushes image, then 1e minikube. |
| 2026-11-24 | Image `ethica79/inference-service:1.0` pushed to Docker Hub (public). Roadmap moved into the repo (`Project/ROADMAP.md`) so both members can see and edit it; proposal PDF in `Project/docs/`. Next: 1e minikube. |
