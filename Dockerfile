FROM python:3.14-slim-trixie AS builder

ARG DEBIAN_FRONTEND=noninteractive
ENV UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/bounty

COPY pyproject.toml ./
RUN uv venv --python /usr/local/bin/python /opt/venv \
    && uv pip install \
        --python /opt/venv/bin/python \
        --prerelease=allow \
        --no-cache \
        --requirements pyproject.toml

FROM python:3.14-slim-trixie

ARG DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/usr/src/admin" \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/admin

COPY --from=builder /opt/venv /opt/venv
COPY . .

CMD ["python", "bounty_agent.py"]
