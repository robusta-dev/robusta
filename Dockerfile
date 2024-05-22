# see https://pythonspeed.com/articles/alpine-docker-python/ for the reason we don't use alpine
FROM python:3.9-slim
RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && apt-get install -y --no-install-recommends ssh socat wget curl libcairo2 python3-dev libffi-dev \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

ENV ENV_TYPE=DEV

RUN mkdir /app
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN /root/.local/bin/poetry config virtualenvs.create false
WORKDIR /app

# Install gcc to compile rumal.yaml.clib, wheel is missing.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && pip3 install --no-cache-dir ruamel.yaml.clib==0.2.8 \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*

# we install the project requirements and install the app in separate stages to optimize docker layer caching
COPY pyproject.toml poetry.lock /app/
RUN /root/.local/bin/poetry install --no-root --no-dev --extras "all"
COPY src/ /app/src
RUN /root/.local/bin/poetry install --no-dev --extras "all"

COPY playbooks/ /etc/robusta/playbooks/defaults
RUN python3 -m pip install --no-cache-dir /etc/robusta/playbooks/defaults

# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]
