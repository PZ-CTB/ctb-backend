# ctb-backend

Jak to uruchomić?

Najpierw w celu zbudowania obrazu wykonaj polecenie:
```
docker build . -t ctb
```

Następnie w celu uruchomienia kontenera:
```
docker run -d -p 8080:8080 ctb
```

Wtedy bedzie można wejść (np przez przeglądarkę) na adres: `https://localhost:8080/`

W celu wyłączenia serwera można wpisać:
```
docker ps
```
Wyświetlą się tam id kontenerów. Aby jakiś ubić należy wykonać polecenie:
```
docker kill <id kontenera>
```
np:
```
docker kill 3fd7d783ce9a
```

A jak komuś się nie chce, to proponuję jednym poleceniem:
```
docker kill `docker container ls -q`
```

Pojedynczy test można wykonywać poleceniem:
```
docker kill `docker container ls -q` ; docker build . -t ctb && docker run -d -p 8080:8080 ctb
```