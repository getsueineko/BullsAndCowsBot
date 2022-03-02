FROM python:3.11.0a5-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /opt/App_BullsAndCows

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apk --update add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction

FROM base as final

COPY --from=builder /opt/App_BullsAndCows/.venv ./.venv
COPY src/ .
CMD [ "./.venv/bin/python", "app.py" ]
