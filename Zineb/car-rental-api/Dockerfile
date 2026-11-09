# 1. Choose a base image
FROM python:3.12-slim

# 2. Set the working directory
WORKDIR /app

# 3. Copy dependencies
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY main.py .

# 6. Document the port
EXPOSE 8000

# 7. Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
