#!/bin/bash

set -e

docker compose build timescaledb-backup
docker compose run --rm timescaledb-backup black .
docker compose run --rm timescaledb-backup ruff check .
docker compose -f ./docker-compose.yml up -d timescaledb postgres_12 postgres_13 postgres_14 postgres_15 postgres_16 postgres_17 postgres_18 minio
docker ps -a
docker compose -f ./docker-compose.yml run --rm timescaledb-backup pytest --cov=app tests/ 
docker compose down
