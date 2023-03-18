FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONOPTIMIZE=TRUE
ENV APPLICATION_ROOT_PATH="/opt/ctb/"
ENV VAR_PATH="/var/ctb/"

RUN apt update
RUN apt upgrade -y
RUN apt install -y sqlite3

RUN mkdir -p $APPLICATION_ROOT_PATH
RUN mkdir -p $VAR_PATH
WORKDIR $APPLICATION_ROOT_PATH

COPY src $APPLICATION_ROOT_PATH/src
COPY res $APPLICATION_ROOT_DIR/res

RUN pip3 install --upgrade pip
RUN ls -la $APPLICATION_ROOT_PATH
RUN pip3 install -r $APPLICATION_ROOT_PATH/src/server/requirements.txt

# tak, w innej kolejności nie zadziała
RUN apt install -y libsasl2-dev python3-dev libldap2-dev libssl-dev
RUN pip3 install pyopenssl 
RUN pip3 install bcrypt secrets


EXPOSE 8080
CMD python3 $APPLICATION_ROOT_PATH/server/main.py