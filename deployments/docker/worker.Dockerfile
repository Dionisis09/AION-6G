FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn requests psutil pydantic
COPY . /app
CMD ["python", "-m", "uvicorn", "app.workers.worker_api:app", "--host", "0.0.0.0", "--port", "8001"]
