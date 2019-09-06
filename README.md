# Microservice for downloading files
The microservice helps main site working. It maintains queries of downloading
archives of files. The microservice can not anything except packing files to
zip archives.
New files are uploaded to the server through the admin panel or FTP.

Creating an archive is done on the fly at the request of a user.
The archive is not saved on the disk instead, as it is sent in parts to
the user to download. 

An archive is protected from unauthorized access by a hash in the address of 
downloading link, for example:
`http://host.ru/archive/3bea29ccabbbf64bdebcc055319c5745/`.

Hash is specified by the name of the directory with the files.
The structure of catalogue looks like:

```
- photos
    - 3bea29ccabbbf64bdebcc055319c5745
      - 1.jpg
      - 2.jpg
      - 3.jpg
    - af1ad8c76fda2e48ea9aed2937e972ea
      - 1.jpg
      - 2.jpg
```


## How to install
The project requires Python 3.7+

```bash
pip install -r requirements.txt
```
or
```bash
pipenv install
```

## How to run
```bash
python server.py
```
or
```bash
pipenv run python server.py
```
Server runs on 8080 port.
Go to the page [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

## How to deploy on server

```bash
python server.py
```
After that, redirect requests starting with `/archive/`.
Example:

```
GET http://host.ru/archive/3bea29ccabbbf64bdebcc055319c5745/
GET http://host.ru/archive/af1ad8c76fda2e48ea9aed2937e972ea/
```

# The project goals
This code was written for learning purpose - Python web-development course
[Devman](https://dvmn.org).