# docker build -t docs -f docs.Dockerfile .
# docker run -it --rm -p 8000:8000 -v ${PWD}:/robusta docs
FROM python:3.9

RUN curl -s https://deb.nodesource.com/setup_16.x | bash
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs  \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
RUN mv /root/.local/bin/poetry /usr/local/bin
WORKDIR /robusta
RUN poetry config virtualenvs.create false
RUN pip install -U robusta-cli --no-cache
COPY . /robusta/
RUN poetry install --extras "all"

CMD ["./docs_autobuild.sh", "--host 0.0.0.0"]