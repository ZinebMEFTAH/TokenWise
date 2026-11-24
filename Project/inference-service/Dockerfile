FROM python:3.12-slim

WORKDIR /app

# Dependencies first: this layer is reused as long as requirements.txt does not change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Run as a normal user, not root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
