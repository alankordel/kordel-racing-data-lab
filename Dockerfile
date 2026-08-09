# syntax=docker/dockerfile:1

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .

COPY src ./src

RUN pip install --no-cache-dir .

COPY config ./config

COPY main.py .

CMD ["python", "main.py"]