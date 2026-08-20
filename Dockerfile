FROM ubuntu:24.04 AS builder

ARG PYTHON_VERSION=3.13
ARG DEBIAN_FRONTEND=noninteractive
ENV UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/python

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/bounty

COPY pyproject.toml ./
RUN uv python install "${PYTHON_VERSION}" \
    && uv venv --python "${PYTHON_VERSION}" /opt/venv \
    && uv pip install \
        --python /opt/venv/bin/python \
        --prerelease=allow \
        --no-cache \
        --requirements pyproject.toml

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/usr/src/admin" \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/admin

COPY --from=builder /opt/python /opt/python
COPY --from=builder /opt/venv /opt/venv
COPY . .

CMD ["python", "bounty_agent.py"]
