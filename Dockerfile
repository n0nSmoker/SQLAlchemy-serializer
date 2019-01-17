FROM python:3.6-alpine3.7

COPY requirements.txt /tmp/base_requirements.txt
COPY tests/requirements.txt /var/www/app/requirements.txt
RUN cat tmp/base_requirements.txt >> /var/www/app/requirements.txt

RUN apk update && \
    apk add build-base postgresql-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install -r /var/www/app/requirements.txt --no-cache-dir && \
    apk del --purge build-base

WORKDIR /var/www/app
ADD . /var/www/app



