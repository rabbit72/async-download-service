FROM python:3.7

RUN apt-get update && apt-get install -y zip && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

COPY . server/
WORKDIR server/
RUN pipenv install --system

EXPOSE 8080

CMD ["python", "server.py"]
