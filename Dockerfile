FROM python:3.13-slim

ENV PATH="/root/.local/bin:/app/.venv/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY . /app

RUN uv sync --frozen

CMD ["python", "-m", "src.scheduler"]
