FROM python:3.11-slim-buster

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "my-app/run.py"]
