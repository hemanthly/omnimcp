FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . "uv>=0.5,<1"

EXPOSE 8000
CMD ["uvicorn", "omnimcp_analytics.gateway:app", "--host", "0.0.0.0", "--port", "8000"]
