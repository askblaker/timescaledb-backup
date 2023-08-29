FROM python:3.11-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y dist-upgrade

RUN apt-get -y install curl ca-certificates gnupg && \ 
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

RUN apt-get update && \
    apt-get -y install postgresql-client-12 && \
    apt-get -y install postgresql-client-13 && \
    apt-get -y install postgresql-client-14 && \
    apt-get -y install postgresql-client-15

COPY ./app/requirements.txt ./

RUN pip install --no-cache-dir -r /app/requirements.txt && \
    rm requirements.txt

COPY ./app/main.py ./app/entrypoint.sh ./
RUN chmod +x ./entrypoint.sh
RUN mkdir backups
RUN groupadd -r tsdbbackup && useradd --no-log-init -r -g tsdbbackup tsdbbackup
RUN chown tsdbbackup:tsdbbackup ./backups
VOLUME /app/backups
USER tsdbbackup

CMD ["./entrypoint.sh"]

