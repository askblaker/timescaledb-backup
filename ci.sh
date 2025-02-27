#!/bin/bash

set -e

docker compose build timescaledb-backup
docker compose run --rm timescaledb-backup poetry run flake8 .
docker compose run --rm timescaledb-backup poetry run black .
docker compose run --rm timescaledb-backup poetry run isort .
docker compose -f ./docker-compose.yml up -d timescaledb postgres_12 postgres_13 postgres_14 postgres_15 postgres_16 postgres_17 minio
docker ps -a
docker compose -f ./docker-compose.yml run --rm timescaledb-backup poetry run pytest --cov=app tests/ 
