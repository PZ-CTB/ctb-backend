FROM python:3.11-alpine

ENV DEBIAN_FRONTEND=noninteractive
ENV APPLICATION_ROOT_PATH="/opt/ctb/"
ENV VAR_PATH="/var/ctb/"

RUN apk --no-cache update && \
    apk --no-cache upgrade && \
    apk --no-cache add \
    gcc musl-dev g++ sqlite libsasl python3-dev openldap-dev openssl-dev

RUN mkdir -p $APPLICATION_ROOT_PATH
RUN mkdir -p $VAR_PATH
WORKDIR $APPLICATION_ROOT_PATH

COPY src/server/requirements.txt /tmp/requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r /tmp/requirements.txt

COPY src $APPLICATION_ROOT_PATH/src
COPY res $APPLICATION_ROOT_PATH/res

ENV PYTHONOPTIMIZE=TRUE
ENV PYTHONPATH=$APPLICATION_ROOT_PATH"/src/:$PYTHONPATH"

EXPOSE 8080
CMD gunicorn --bind=0.0.0.0:8080 server.main:app
