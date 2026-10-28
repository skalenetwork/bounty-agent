FROM python:3.14.10-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-cache --python /usr/local/bin/python

FROM python:3.14.10-slim-trixie

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . .

STOPSIGNAL SIGINT

CMD ["python", "bounty_agent.py"]
