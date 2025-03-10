ARG GST_DOCKER_IMAGE_PREFIX="ghcr.io/gamestonkterminal"
ARG GST_DOCKER_PYTHON_VERSION="1.0.0"
FROM ${GST_DOCKER_IMAGE_PREFIX}/gst-python:${GST_DOCKER_PYTHON_VERSION}

COPY --chown=python:python pyproject.toml poetry.lock /home/python/

RUN mkdir /home/python/gamestonk_terminal && \
  touch gamestonk_terminal/__init__.py && \
  chown python:python /home/python/gamestonk_terminal /home/python/gamestonk_terminal/__init__.py && \
  poetry install && \
  poetry install -E prediction
