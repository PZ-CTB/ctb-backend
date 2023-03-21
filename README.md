# ctb-backend

## How to run the server in a Docker container?

Create an image:
```
docker build . -t ctb
```

Start container:
```
docker run -d -p 8080:8080 ctb
```

Test connection (in your browser): `https://localhost:8080/`.

To shutdown the server, type:
```
docker ps
```
The command shows ids of containers. To kill the container, execute the command:
```
docker kill <id of the container>
```
f.e.:
```
docker kill 3fd7d783ce9a
```

Or just type the following command to kill all containers:
```
docker kill `docker container ls -q`
```

Whole test (killing old, building and starting the new one) can be done with one command:
```
docker kill `docker container ls -q` ; docker build . -t ctb && docker run -d -p 8080:8080 ctb
```

In case of necessity of saving the database between every start of the container,
it can be achieved by binding of container's directory with host's directory.
The destination directory on the host must be created before the binding.
For example, for storing the database in */tmp/ctb_opt*, execute the following command:
```
mkdir -p /tmp/ctb_opt
docker run -d -p 8080:8080 --mount type=bind,source=/tmp/ctb_opt,target=/var/ctb ctb
```

To run everything using one command, execute:
```
mkdir -p /tmp/ctb_opt && docker kill `docker container ls -q` ; docker build . -t ctb && docker run -d -p 8080:8080 --mount type=bind,source=/tmp/ctb_opt,target=/var/ctb ctb
```
