FROM python:3.5
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get -y install uuid-dev

RUN mkdir -p /webapp
COPY ./requirements /webapp/requirements
WORKDIR /webapp

RUN pip install --upgrade pip
RUN pip install -r requirements/develop.txt \
    && pip install ipdb
