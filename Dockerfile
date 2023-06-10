FROM python:3.10-slim

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/
RUN apt update && apt install -y curl git

WORKDIR /app
RUN curl -sSL https://install.python-poetry.org/ | python -
COPY pyproject.toml poetry.lock ./
RUN /root/.local/share/pypoetry/venv/bin/poetry config virtualenvs.create false
RUN /root/.local/share/pypoetry/venv/bin/poetry install --no-dev --no-interaction --no-ansi

COPY filler ./filler
COPY scripts ./scripts
COPY main.py logging_config.yaml ./
ENTRYPOINT ["/app/scripts/entrypoint"]
