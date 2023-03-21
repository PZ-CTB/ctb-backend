# ctb-backend

## How to run

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

Jeśli nie chcemy, aby baza danych nie była tworzona za każdym razem, można wykonać bindowanie
katalogu podczas uruchamiania kontenera. Wcześniej należy utworzyć odpowiedni katalog na naszym
komputerze. Przykładowo, aby baza danych była w katalogi <i>/tmp/ctb_opt</i>
należy wykonać polecenia:
```
mkdir -p /tmp/ctb_opt
docker run -d -p 8080:8080 --mount type=bind,source=/tmp/ctb_opt,target=/var/ctb ctb
```

Lub w jednej linijce, włączając w to restart starego kontenera:
```
mkdir -p /tmp/ctb_opt && docker kill `docker container ls -q` ; docker build . -t ctb && docker run -d -p 8080:8080 --mount type=bind,source=/tmp/ctb_opt,target=/var/ctb ctb
```
