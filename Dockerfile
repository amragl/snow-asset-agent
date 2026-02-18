FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim

# Non-root user
RUN adduser --disabled-password --gecos "" agent
WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ src/

# py.typed marker
COPY src/snow_asset_agent/py.typed src/snow_asset_agent/py.typed

RUN pip install --no-cache-dir -e .

USER agent

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from snow_asset_agent import __version__; print(__version__)"

ENTRYPOINT ["python", "-m", "snow_asset_agent"]
