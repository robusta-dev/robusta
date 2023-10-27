# Use the specific version of Python as the base image
FROM python:3.10.12


RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs  \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN mv /root/.local/bin/poetry /usr/local/bin

# Set the working directory in the Docker image
WORKDIR /robusta

COPY . /robusta/

# Configure poetry and install packages
RUN poetry config virtualenvs.create false
RUN poetry install --extras "all"

# Command to run Streamlit when the container starts
CMD ["streamlit", "run", "./scripts/main_app.py"]
