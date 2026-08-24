FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN uv sync --frozen --no-dev

EXPOSE 8000
ENTRYPOINT ["uv", "run", "delphi-backend"]
