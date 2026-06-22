# Timescaledb-backup

1. Back up and restore timescaledb or vanilla postgres databases
2. Both single use and at scheduled intervals (daily/hourly)
3. Store and restore backups locally or on a Minio S3 bucket
4. Progressive and configurable storage schema
5. Restore to timescaledb or vanilla postgres
6. Restore with multiple workers for high speed
7. Supports postgres 12, 13, 14, 15, 16, 17, 18 and timescaledb 2.0+

# Examples

See more examples in the `examples/` folder in the repo.

## Regular backups at 15:30

### docker run

```sh
docker volume create timescaledb-backups
docker run -v timescaledb-backups:/app/backups \
-e POSTGRES_HOST=postgres.your.host.com \
-e POSTGRES_USER=your_postgres_username \
-e POSTGRES_DB=your_postgres_db_name \
-e MODE=daily_15_30 \
askblaker/timescaledb-backup:0.4.0
```

### docker compose

```yaml
services:
  timescaledb:
    image: timescale/timescaledb-postgis:2.1.0-pg12
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb

  timescaledb-backup:
    image: askblaker/timescaledb-backup:0.4.0
    volumes:
      - timescaledb-backup:/app/backups
    environment:
      POSTGRES_HOST: timescaledb
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
-e MODE=run_single_backup \
askblaker/timescaledb-backup
```

## Restore from s3 bucket

```bash
docker run --rm --network=mynet \
-e POSTGRES_HOST=tsdb \
-e POSTGRES_USER=postgres \
-e POSTGRES_DB=your_db \
-e S3_ENDPOINT=your.host.com \
-e S3_ACCESS_KEY=verysecretaccesskey \
-e S3_SECRET_KEY=verysecretsecretkey \
-e S3_SECURE=true \
-e RESTORE_OVERWRITE=true \
-e MODE=restore_latest_s3_file \
askblaker/timescaledb-backup
```

## MODE values

| Value                        | Behavior                                              |
| ---------------------------- | ---------------------------------------------------- |
| `hourly_MM`                  | Run a backup every hour at minute `MM` (e.g. `hourly_00`) |
| `daily_HH_MM`                | Run a backup every day at `HH:MM` (e.g. `daily_15_30`)   |
| `run_single_backup`          | Run one backup and exit                              |
| `restore_latest_local_file`  | Restore from the latest local backup file and exit  |
| `restore_latest_s3_file`     | Download the latest backup from S3, restore it and exit |

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
| KEEP_DAYS         | 7                  |
| KEEP_WEEKS        | 4                  |
| KEEP_MONTHS       | 6                  |
| S3_ENDPOINT       | minio:9000         |
| S3_REGION         |                    |
| S3_BUCKET_NAME    | timescaledb-backup |
| S3_ACCESS_KEY     | minioadmin         |
| S3_SECRET_KEY     | minioadmin         |
| S3_SECURE         | false              |
| S3_UPLOAD         | false              |
| MODE              | hourly_00          |
| RESTORE_OVERWRITE | false              |
| LOGLEVEL          | INFO               |

# Development

All development can be done through Docker - no need to install Python or uv locally.

## Build dev

```sh
docker compose build timescaledb-backup
```

## Build production

```sh
docker build -t timescaledb-backup .
```

## Run tests

```sh
docker compose up -d minio timescaledb postgres_12 postgres_13 postgres_14 postgres_15 postgres_16 postgres_17
docker compose run --rm timescaledb-backup pytest --cov=app --cov-report=html
```

Or run the full pipeline (build, format, lint, test) with `./ci.sh`.

## Update dependencies (requires uv locally)

Dependencies are declared in `app/pyproject.toml` and pinned in `app/uv.lock`.
To update the lock file, install [uv](https://docs.astral.sh/uv/) and run:

```sh
cd app
uv lock
```

Commit the updated `uv.lock` so the Docker builds (`uv sync --frozen`) stay reproducible.

# Test coverage

Run the tests as above and open the report in the **htmlcov** folder.
