# see https://pythonspeed.com/articles/alpine-docker-python/ for the reason we don't use alpine
FROM python:3.8-slim-bullseye
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
RUN pip3 install poetry==1.1.6
RUN poetry config virtualenvs.create false
COPY src/pyproject.toml /app
COPY src/poetry.lock /app
WORKDIR /app
RUN bash -c "pip3 install --requirement <(poetry export --dev --format requirements.txt --without-hashes)"

ADD src/ /app

RUN pip3 install --use-feature=in-tree-build .

COPY playbooks/ /etc/robusta/playbooks/defaults
RUN pip3 install -r /etc/robusta/playbooks/defaults/requirements.txt
# remove the requirements so that we don't reinstall them at runtime
RUN rm /etc/robusta/playbooks/defaults/requirements.txt
# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]