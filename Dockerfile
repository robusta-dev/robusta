# see https://pythonspeed.com/articles/alpine-docker-python/ for the reason we don't use alpine
FROM python:3.9-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ssh socat wget curl libcairo2 python3-dev libffi-dev socat \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# install a custom version of socat with readline enabled
# disabled because of an issue with the libreadline7 dependency
#RUN wget https://launchpad.net/~ionel-mc/+archive/ubuntu/socat/+build/15532886/+files/socat_1.7.3.2-2ubuntu2ionelmc2~ppa1_amd64.deb
#RUN dpkg -i socat_1.7.3.2-2ubuntu2ionelmc2~ppa1_amd64.deb
ENV ENV_TYPE=DEV

# we install the project requirements and install the app in separate stages to optimize docker layer caching
RUN mkdir /app
RUN pip3 install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.2.0b1 
RUN /root/.local/bin/poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock /app/
WORKDIR /app

# Install gcc to compile rumal.yaml.clib, wheel is missing.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && pip3 install ruamel.yaml.clib \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*

RUN /root/.local/bin/poetry install --no-root --extras "all"

COPY src/ /app/src

RUN pip3 install .
# Install tabulate version that fixes column width wrapping. Cannot be added to pypi as a git dependency, so adding it here
RUN pip3 install git+https://github.com/astanin/python-tabulate.git@b2c26bcb70e497f674b38aa7e29de12c0123708a#egg=tabulate

COPY playbooks/ /etc/robusta/playbooks/defaults

RUN python3 -m pip install /etc/robusta/playbooks/defaults

# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]