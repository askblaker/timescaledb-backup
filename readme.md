# Timescaledb-backup

1. Back up and restore timescaledb or vanilla postgres databases
2. Both single use and at scheduled intervals (daily/hourly)
3. Store and restore backups locally or on a Minio S3 bucket
4. Progressive and configurable storage schema
5. Restore to timescaledb or vanilla postgres
6. Restore with multiple workers for high speed
7. Supports postgres 12, 13, 14, 15 and timescaledb 2.0 +

# Examples

Se more examples in the examples files in the repo.

## Regular backups at 15:30

### docker run

```sh
docker volume create timescaledb-backups
docker run -v timescaledb-backups:/app/backups \
-e POSTGRES_HOST=postgres.your.host.com \
-e POSTGRES_USER=your_postgres_username \
-e POSTGRES_DB=your_postgres_db_name \
-e MODE=daily_15_30 \
askblaker/timescaledb-backup:0.1.0
```

### docker-compose

```yaml
version: "3"
services:
  timescaledb:
    image: timescale/timescaledb-postgis:2.1.0-pg12
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb

  timescaledb-backup:
    image: askblaker/timescaledb-backup
    volumes: timescaledb-backup:/app/backups
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
      MODE: daily_15_30

volumes:
  timescaledb-backup:
```

## One time backup to mounted volume

```sh
mkdir my-host-dir
chmod 777 -R my-host-dir
docker run --rm -v ./my-host-dir:/app/backups \
-e POSTGRES_HOST=postgres.your.host.com \
-e POSTGRES_USER=your_postgres_username \
-e POSTGRES_DB=your_postgres_db_name \
-e MODE=run_single_backup
askblaker/timescaledb-backup
```

## Restore from s3 bucket

```bash
docker run --rm --network=mynet \
-e POSTGRES_HOST=tsdb
-e POSTGRES_USER=postgres
-e POSTGRES_DB=your_db
-e S3_ENDPOINT=your.host.com
-e S3_ACCESS_KEY=verysecretaccesskey
-e S3_SECRET_KEY=verysecretsecretkey
-e S3_SECURE=true
-e RESTORE_OVERWRITE=true
-e MODE=restore_latest_local_file
askblaker/timescaledb-backup
```

## Environment variables

| Variable          | Default            |
| ----------------- | ------------------ |
| POSTGRES_HOST     | timescaledb        |
| POSTGRES_PORT     | 5432               |
| POSTGRES_DB       | mydb               |
| POSTGRES_PASSWORD | password           |
| POSTGRES_USER     | postgres           |
| TIMESCALE         | true               |
| KEEP_LOCAL_COPIES | true               |
| KEEP_LAST_HOURS   | 6                  |
| KEEP_LAST_DAYS    | 7                  |
| KEEP_LAST_MONTHS  | 4                  |
| S3_ENDPOINT       | minio:9000         |
| S3_REGION         |                    |
| S3_BUCKET_NAME    | timescaledb-backup |
| S3_ACCESS_KEY     | minioadmin         |
| S3_SECRET_KEY     | minioadmin         |
| S3_SECURE         | false              |
| S3_UPLOAD         | false              |
| MODE              | hourly_00          |
| BACKUP_FOLDER     | backups            |
| RESTORE_OVERWRITE | false              |

# Development

## Freeze production requirements.txt  
```sh
# in ./app folder
poetry export --without dev --format=requirements.txt > ./requirements.txt  
```

## Build dev

```sh
docker-compose build timescaledb-backup
```

## Build production

```sh
docker build -t timescaledb-backup .
```

## Run tests

```sh
docker-compose up -d minio timescaledb postgres_12 postgres_13 postgres_14 postgres_15
docker-compose run --rm timescaledb-backup pytest --cov=app --cov-report=html
```

# Test coverage

Run tests and see in the **htmlcov** folder
