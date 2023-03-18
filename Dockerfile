FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV APPLICATION_ROOT_PATH="/opt/ctb/"
ENV VAR_PATH="/var/ctb/"

RUN apt update
RUN apt upgrade -y
RUN apt install -y sqlite3 libsasl2-dev python3-dev libldap2-dev libssl-dev

RUN mkdir -p $APPLICATION_ROOT_PATH
RUN mkdir -p $VAR_PATH
WORKDIR $APPLICATION_ROOT_PATH

COPY src $APPLICATION_ROOT_PATH/src
COPY res $APPLICATION_ROOT_PATH/res

RUN pip3 install --upgrade pip
RUN pip3 install -r $APPLICATION_ROOT_PATH/src/server/requirements.txt
# poniższe muszą być instalowane w drugiej turze
RUN pip3 install bcrypt secrets 

ENV PYTHONOPTIMIZE=TRUE
ENV CERT_KEY_FILE=$APPLICATION_ROOT_PATH"res/cert/example.key"
ENV CERT_FILE=$APPLICATION_ROOT_PATH"res/cert/example.crt"
ENV PYTHONPATH=$APPLICATION_ROOT_PATH"/src/:$PYTHONPATH"

EXPOSE 8080
CMD gunicorn --keyfile $CERT_KEY_FILE --certfile $CERT_FILE --bind 0.0.0.0:8080 server.main:app 