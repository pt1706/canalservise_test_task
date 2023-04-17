FROM python:3.10-alpine3.17
LABEL maintainer="t89213064699@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

RUN python -m venv /py
RUN /py/bin/pip install --upgrade pip
RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
       build-base postgresql-dev musl-dev zlib zlib-dev linux-headers
RUN /py/bin/pip install -r /tmp/requirements.txt
RUN rm -rf /tmp
RUN apk del .tmp-build-deps

ENV PATH="/py/bin:$PATH"



