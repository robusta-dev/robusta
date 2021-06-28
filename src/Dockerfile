# see https://pythonspeed.com/articles/alpine-docker-python/ for the reason we don't use alpine
FROM python:3.8-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ssh socat wget curl libcairo2 python3-dev libffi-dev \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# install a custom version of socat with readline enabled
RUN wget https://launchpad.net/~ionel-mc/+archive/ubuntu/socat/+build/15532886/+files/socat_1.7.3.2-2ubuntu2ionelmc2~ppa1_amd64.deb
RUN dpkg -i socat_1.7.3.2-2ubuntu2ionelmc2~ppa1_amd64.deb

ENV CUSTOM_PLAYBOOKS_ROOT=/etc/robusta/config
ENV ENV_TYPE=DEV

# we install the project requirements and install the app in separate stages to optimize docker layer caching
RUN mkdir /app
RUN pip3 install --upgrade pip
RUN pip3 install poetry==1.1.6
RUN poetry config virtualenvs.create false
COPY pyproject.toml /app
COPY poetry.lock /app
WORKDIR /app
RUN bash -c "pip3 install --requirement <(poetry export --dev --format requirements.txt --without-hashes)"

COPY . /app

RUN pip3 install --use-feature=in-tree-build .

# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]