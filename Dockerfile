ARG WORKDIR=/bot

FROM python:3.13.0a4-alpine AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    # OPTIONAL. Fix some troubles with files.pythonhosted.org timeout. Default is 15s
    PIP_DEFAULT_TIMEOUT=100 \
    # Turns off buffering for easier container logging
    PYTHONUNBUFFERED=1 \
    # Keeps Python from generating .pyc files in the container
    PYTHONDONTWRITEBYTECODE=1 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    # POETRY_VIRTUALENVS_CREATE=1 \
    # POETRY_VIRTUALENVS_IN_PROJECT=1 \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    # Set local repo
    POETRY_VERSION=1.4.0

RUN apk --update add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo curl

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION  
ENV PATH="${PATH}:/opt/poetry/bin"

ARG WORKDIR
WORKDIR $WORKDIR

RUN python -m venv "${WORKDIR}/.venv"
ENV PATH="${WORKDIR}/.venv/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN unset https_proxy \
  && poetry install --only main

COPY src/ .

RUN chmod -R g+rwX $WORKDIR


FROM python:3.13.0a4-alpine AS final

ARG WORKDIR
WORKDIR $WORKDIR
RUN chmod -R g+rwX $WORKDIR

COPY --from=builder $WORKDIR $WORKDIR
ENV PATH="${WORKDIR}/.venv/bin:$PATH"

USER 1024

CMD [ "python", "app.py" ]
