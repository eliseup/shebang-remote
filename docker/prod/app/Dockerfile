### Builder stage
FROM python:3.12-slim-bookworm AS builder

COPY src/requirements.txt /tmp

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev build-essential && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r /tmp/requirements.txt


### Final stage.
FROM python:3.12-slim-bookworm

# Python deps
COPY --from=builder /tmp/wheels /tmp/wheels

# APT packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install --no-cache --no-cache-dir /tmp/wheels/* && \
    rm -rf /tmp/wheels && \
    # User settings and environment
    addgroup --gid 1000 --system app && \
    adduser --uid 1000 --system --group app && \
    mkdir -p /usr/src/server

# Application files
COPY src/server /usr/src/server
RUN chown app. /usr/src/server -R

WORKDIR /usr/src/server
USER app

CMD ["fastapi", "run", "main.py"]
