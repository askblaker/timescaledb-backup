```bash
docker network create mynet
```

```bash
docker run -d --name tsdb --network=mynet -p 5432:5432 `
-e POSTGRES_PASSWORD=password `
timescale/timescaledb-postgis:2.0.1-pg12
```

### Restore the db into it

```powershell
docker run --rm -it --network=mynet `
-e POSTGRES_HOST=tsdb `
-e POSTGRES_USER=postgres `
-e POSTGRES_DB=mydb `
-e S3_ENDPOINT=minio.mydomain.com `
-e S3_ACCESS_KEY=access_key `
-e S3_SECRET_KEY=secret_key `
-e S3_SECURE=true `
-e RESTORE_OVERWRITE=false `
-e MODE=restore_latest_s3_file `
askblaker/timescaledb-backup
```
