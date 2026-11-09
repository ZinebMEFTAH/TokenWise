# Zineb – Car Rental API (FastAPI + Docker)

Docker image: `zineb36/tokenwise:1.0` → https://hub.docker.com/r/zineb36/tokenwise
Source code: [`car-rental-api/`](car-rental-api/)

## 1. Mini application

A REST API in Python with FastAPI. The cars are stored in an in-memory list.

| Method | Path | Action |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/cars` | List all cars |
| GET | `/cars/{car_id}` | Get one car (404 if not found) |
| POST | `/cars` | Create a car (201) |
| PUT | `/cars/{car_id}` | Update a car |
| DELETE | `/cars/{car_id}` | Delete a car |

The request body is validated with a Pydantic model (`Car`: `id`, `brand`, `model`, `available`).

Run it locally:
```bash
cd car-rental-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Interactive docs: http://localhost:8000/docs

## 2. Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
- `requirements.txt` is copied before the code so the dependency layer stays cached.
- `--host 0.0.0.0` makes the app reachable from outside the container.
- `.dockerignore` excludes `venv/`, `__pycache__/`, `.git/`, `.DS_Store`.

## 3. Build and run the image

```bash
docker build -t car-rental-api .
docker run -d -p 8000:8000 --name car-rental car-rental-api
```
Test: http://localhost:8000/docs

## 4. Publish to Docker Hub

```bash
docker login
docker buildx build --platform linux/amd64,linux/arm64 -t zineb36/tokenwise:1.0 --push .
```
The image is built for both Intel/AMD and ARM (Apple Silicon), so it runs on either.

Run it from anywhere:
```bash
docker run -p 8000:8000 zineb36/tokenwise:1.0
```

## 5. Publish to GitHub

`.gitignore` excludes `venv/`, `__pycache__/`, `.env`, `.DS_Store`, `.vscode/`.

```bash
git add Zineb/car-rental-api
git commit -m "Add car rental FastAPI app with Dockerfile"
git push origin main
```
