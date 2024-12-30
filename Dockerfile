FROM python:3.12-slim

RUN mkdir /app
WORKDIR /app

ENV PYTHONUNBUFFERED=1

ADD . /app
ADD requirements.txt requirements.txt

RUN apt update -y
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "-u", "main.py"]
