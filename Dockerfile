# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

EXPOSE 8080

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=TRUE

# Install dependencies
RUN apt update && \
    apt upgrade -y && \
    apt install -y libsasl2-dev libldap2-dev libssl-dev libpq5

# Install pip requirements
COPY src/server/requirements.txt /tmp/requirements-server.txt
COPY src/model/requirements.txt /tmp/requirements-model.txt
RUN cat /tmp/requirements-server.txt /tmp/requirements-model.txt | sort -u > /tmp/requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m pip install -r /tmp/requirements.txt
RUN rm -f /tmp/requirements*.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "src.server.main:create_app()"]
