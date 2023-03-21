# ctb-backend

## How to run

At the beginig you must create an image:
```
docker build . -t ctb
```

The next step is starting container. For that you must type:
```
docker run -d -p 8080:8080 ctb
```

And then you should be able to open (in your browser) address: `https://localhost:8080/`.

To shutdown the server, type:
```
docker ps
```
The command shows ids of containers. To kill the container, you must execute the command:
```
docker kill <id of the container>
```
f.e.:
```
docker kill 3fd7d783ce9a
```

If someone does not want searching the id, they could execute one command:
```
docker kill `docker container ls -q`
```

Whole test (killing old, building and starting the new one) can be done with one command:
```
docker kill `docker container ls -q` ; docker build . -t ctb && docker run -d -p 8080:8080 ctb
```

In case of necessity of saving the database between every start of container,
it should be done binding of container's directory with host's directory.
The destination directory on the host must be created befor the binding.
For example, for storing the database in <i>/tmp/ctb_opt</i>,
it must be execuuted the following command:
```
mkdir -p /tmp/ctb_opt
docker run -d -p 8080:8080 --mount type=bind,source=/tmp/ctb_opt,target=/var/ctb ctb
```

Or if someone want do everything in one test, they should execute:
```
mkdir -p /tmp/ctb_opt && docker kill `docker container ls -q` ; docker build . -t ctb && docker run -d -p 8080:8080 --mount type=bind,source=/tmp/ctb_opt,target=/var/ctb ctb
```
