import logging
import os
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd
import psycopg2
import schedule
from isoweek import Week
from minio import Minio

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

config = {
    "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", "timescaledb"),
    "POSTGRES_PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
    "POSTGRES_DB": os.environ.get("POSTGRES_DB", "mydb"),
    "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
    "POSTGRES_USER": os.environ.get("POSTGRES_USER", "postgres"),
    "TIMESCALE": os.environ.get("TIMESCALE", "True").lower() in ["true", "1"],
    "KEEP_LOCAL_COPIES": os.environ.get("KEEP_LOCAL_COPIES", "True").lower() in ["true", "1"],
    "KEEP_LAST_HOURS": int(os.environ.get("KEEP_LAST_HOURS", "6")),
    "KEEP_LAST_DAYS": int(os.environ.get("KEEP_DAYS", "7")),
    "KEEP_LAST_WEEKS": int(os.environ.get("KEEP_WEEKS", "4")),
    "KEEP_LAST_MONTHS": int(os.environ.get("KEEP_MONTHS", "6")),
    "S3_ENDPOINT": os.environ.get("S3_ENDPOINT", "minio:9000"),
    "S3_REGION": os.environ.get("S3_REGION"),
    "S3_BUCKET_NAME": os.environ.get("S3_BUCKET_NAME", "timescaledb-backup"),
    "S3_ACCESS_KEY": os.environ.get("S3_ACCESS_KEY", "minioadmin"),
    "S3_SECRET_KEY": os.environ.get("S3_SECRET_KEY", "minioadmin"),
    "S3_SECURE": os.environ.get("S3_SECURE", "False").lower() in ["true", "1"],
    "S3_UPLOAD": os.environ.get("S3_UPLOAD", "False").lower() in ["true", "1"],
    "MODE": os.environ.get("MODE", "hourly_00"),
    "BACKUP_FOLDER": "backups",
    "RESTORE_OVERWRITE": os.environ.get("RESTORE_OVERWRITE", "False").lower() in ["true", "1"],
}


minio_client = Minio(
    endpoint=config["S3_ENDPOINT"],
    access_key=config["S3_ACCESS_KEY"],
    secret_key=config["S3_SECRET_KEY"],
    secure=config["S3_SECURE"],
    region=config["S3_REGION"],
)


def get_psycopg2_conn(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    dbname=config["POSTGRES_DB"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
):
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        connect_timeout=3,
    )


def database_exists(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
    database=config["POSTGRES_DB"],
):
    result = subprocess.run(
        (
            f"env PGPASSWORD={password} "
            f"psql "
            f"-h {host} "
            f"-p {port} "
            f"-U {user} "
            f"-d {database} "
            f'-c "SELECT datname FROM pg_database where datistemplate = false"'
        ),
        shell=True,
        capture_output=True,
        text=True,
    )
    if len(result.stderr) > 0:
        if result.stderr.find("does not exist") != -1:
            return False
        else:
            for line in result.stderr.splitlines():
                log.error(line)
            sys.exit()
    else:
        return True


def get_timescale_version(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
):
    with get_psycopg2_conn(host=host, port=port, user=user, password=password) as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                SELECT installed_version  
                FROM pg_available_extensions
                WHERE name = 'timescaledb';
                """  # noqa: W291
            )
            result = cur.fetchone()
            if result is not None:
                return result[0]


def get_pg_major_version(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
):
    with get_psycopg2_conn(host=host, port=port, user=user, password=password) as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("show server_version;")
            result = cur.fetchone()
            return result[0][:2]


def delete_db(
    database=config["POSTGRES_DB"],
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
    pg_version="12",
):
    result = subprocess.run(
        (f"env PGPASSWORD={password} dropdb --cluster {pg_version}/{host}:{port} -U {user} {database}"),
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.stdout is not None:
        for line in result.stdout.splitlines():
            log.info(line)
        for line in result.stderr.splitlines():
            log.error(line)


def get_time_string():
    return time.strftime("%Y%m%d%H%M%S")


def run_backup_job(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    database=config["POSTGRES_DB"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
):
    log.info("Starting backup...")
    t1 = datetime.now()
    if config["TIMESCALE"]:
        timescale_version = get_timescale_version(host, port)
    else:
        timescale_version = "none"

    timestr = get_time_string()
    pg_major_version = get_pg_major_version(host, port)
    filename = f"{timestr}_DB-{database}_PG-{pg_major_version}_TS-{timescale_version}.bak"
    filepath = f"./{config['BACKUP_FOLDER']}/{filename}"

    result = subprocess.run(
        (
            f"env PGPASSWORD={password} "
            f"pg_dump "
            f"--cluster {pg_major_version}/{host}:{port} "
            f"-U {user} "
            f"-Fc "
            f"-f  {filepath}"
            f" {database} "
        ),
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.stdout is not None:
        for line in result.stdout.splitlines():
            log.info(line)
        for line in result.stderr.splitlines():
            log.error(line)

    t2 = datetime.now()
    delta = t2 - t1
    log.info(f"Backup completed in {delta}")
    return filename


def restore_db_from_latest_file(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    database=config["POSTGRES_DB"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
):
    log.info("Starting restore")
    t1 = datetime.now()
    file_list = list_files_in_folder_desc(config["BACKUP_FOLDER"])
    if file_list == []:
        raise FileNotFoundError("No backup files found!")

    filename = f'./{config["BACKUP_FOLDER"]}/{list_files_in_folder_desc(config["BACKUP_FOLDER"])[0]}'
    dbix = filename.find("DB-")
    if dbix != -1:
        db_end = filename.find("_", dbix)
        db_name = filename[dbix + 3 : db_end]  # noqa E203
    else:
        raise FileNotFoundError("No suitable backup file found!")

    pg_version_ix = filename.find("PG-")
    if pg_version_ix != -1:
        pg_major_version = filename[pg_version_ix + 3 : pg_version_ix + 5]  # noqa E203

    if database_exists(database=db_name):
        if config["RESTORE_OVERWRITE"]:
            log.info("Deleting old database!")
            delete_db(db_name)
        else:
            raise FileExistsError("Database already exists! Set RESTORE_OVERWRITE=true if you want to overwrite!")
    log.info(f"Creating new database {database}")
    result = subprocess.run(
        (f"env PGPASSWORD={password} createdb --cluster {pg_major_version}/{host}:{port} -U {user} {database}"),
        shell=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        log.info(line)
    for line in result.stderr.splitlines():
        log.error(line)

    timescale_schema = ""
    if config["TIMESCALE"]:
        timescale_schema = "-N _timescaledb_catalog "
        with get_psycopg2_conn(host=host, port=port, dbname=database) as pg_conn:
            with pg_conn.cursor() as cur:
                pre_restore_sql = "select timescaledb_pre_restore();"
                log.info(pre_restore_sql)
                cur.execute(pre_restore_sql)
                log.info(cur.fetchone())
                result = subprocess.run(
                    (
                        f"env PGPASSWORD={password} "
                        f"pg_restore "
                        f"-Fc "
                        f"--cluster {pg_major_version}/{host}:{port} "
                        f"-n _timescaledb_catalog "
                        f"-U {user} "
                        f"-d {database} "
                        f" {filename} "
                    ),
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                if result.stdout is not None:
                    for line in result.stdout.splitlines():
                        log.info(line)
                    for line in result.stderr.splitlines():
                        log.error(line)

    result = subprocess.run(
        (
            f"env PGPASSWORD={password} "
            f"pg_restore "
            f"-Fc "
            f"--cluster {pg_major_version}/{host}:{port} "
            f"{timescale_schema}"
            f"-U {user} "
            f"-d {database} "
            f"-j 4 "
            f" {filename} "
        ),
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.stdout is not None:
        for line in result.stdout.splitlines():
            log.info(line)
        for line in result.stderr.splitlines():
            log.error(line)

    if config["TIMESCALE"]:
        with get_psycopg2_conn(config["POSTGRES_HOST"], config["POSTGRES_PORT"], db_name) as pg_conn:
            with pg_conn.cursor() as cur:
                post_restore_sql = "SELECT timescaledb_post_restore();"
                log.info(post_restore_sql)
                cur.execute(post_restore_sql)
                log.info(cur.fetchone())

    t2 = datetime.now()
    delta = t2 - t1
    log.info(f"Restore completed in {delta}")


def list_files_in_folder_desc(folder=config["BACKUP_FOLDER"]):
    raw_list = os.listdir(f"./{folder}")
    if raw_list is not None:
        return sorted(raw_list, key=lambda x: x.split("_")[0], reverse=True)


def prune_old_local_backup_files_except(keep_files):
    for filename in list_files_in_folder_desc(config["BACKUP_FOLDER"]):
        filepath = f'./{config["BACKUP_FOLDER"]}/{filename}'
        if filename not in keep_files and os.path.exists(filepath):
            os.remove(filepath)


def upload_file_to_s3_bucket(
    file,
    endpoint=config["S3_ENDPOINT"],
    access_key=config["S3_ACCESS_KEY"],
    secret_key=config["S3_SECRET_KEY"],
    secure=config["S3_SECURE"],
    bucket_name=config["S3_BUCKET_NAME"],
):
    if minio_client.bucket_exists(bucket_name):
        pass
    else:
        minio_client.make_bucket(bucket_name)

    minio_client.fput_object(
        bucket_name,
        file,
        f'./{config["BACKUP_FOLDER"]}/{file}',
    )


def list_files_in_s3_bucket_desc(
    bucket=config["S3_BUCKET_NAME"],
    endpoint=config["S3_ENDPOINT"],
    access_key=config["S3_ACCESS_KEY"],
    secret_key=config["S3_SECRET_KEY"],
    secure=config["S3_SECURE"],
    bucket_name=config["S3_BUCKET_NAME"],
):
    file_list = []
    objects = minio_client.list_objects(bucket)
    for obj in objects:
        file_list.append(obj.object_name)
    return sorted(file_list, key=lambda x: x.split("_")[0], reverse=True)


def prune_old_s3_files_except(
    keep_files,
    endpoint=config["S3_ENDPOINT"],
    access_key=config["S3_ACCESS_KEY"],
    secret_key=config["S3_SECRET_KEY"],
    secure=config["S3_SECURE"],
    bucket_name=config["S3_BUCKET_NAME"],
):
    if minio_client.bucket_exists(bucket_name):
        pass
    else:
        log.error("Tried purging non existing s3 bucket, exiting.")
        sys.exit()

    for filename in list_files_in_s3_bucket_desc(config["S3_BUCKET_NAME"]):
        if filename not in keep_files:
            minio_client.remove_object(config["S3_BUCKET_NAME"], filename)


def download_latest_s3_file(
    endpoint=config["S3_ENDPOINT"],
    access_key=config["S3_ACCESS_KEY"],
    secret_key=config["S3_SECRET_KEY"],
    secure=config["S3_SECURE"],
    bucket_name=config["S3_BUCKET_NAME"],
):
    log.info("Downloading latest file from s3")
    object_name = list_files_in_s3_bucket_desc()[0]
    log.info(f"{object_name}")
    minio_client.fget_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=f"./{config['BACKUP_FOLDER']}/{list_files_in_s3_bucket_desc()[0]}",
    )


def get_file_info_dataframe(
    filenames,
    keep_last_hours=config["KEEP_LAST_HOURS"],
    keep_last_days=config["KEEP_LAST_DAYS"],
    keep_last_weeks=config["KEEP_LAST_WEEKS"],
    keep_last_months=config["KEEP_LAST_MONTHS"],
):
    datetimes = []
    age_weeks = []
    age_timedeltas = []
    age_hours = []
    age_days = []
    age_months = []
    for filename in filenames:
        dt = datetime(
            year=int(filename[:4]),
            month=int(filename[4:6]),
            day=int(filename[6:8]),
            hour=int(filename[8:10]),
            minute=int(filename[8:10]),
            second=int(filename[10:12]),
        )

        dt_day_only = datetime(year=int(filename[:4]), month=int(filename[4:6]), day=int(filename[6:8]))
        dt_now_day_only = datetime(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        age_timedelta = datetime.now() - dt
        age_hour = int(age_timedelta.total_seconds() / 3600)
        age_day = (dt_now_day_only - dt_day_only).days
        age_month = (datetime.now().year - dt.year) * 12 + (datetime.now().month - dt.month)

        datetimes.append(dt)
        age_weeks.append(Week.thisweek() - Week.withdate(dt))
        age_timedeltas.append(age_timedelta)
        age_hours.append(age_hour)
        age_days.append(age_day)
        age_months.append(age_month)

    df = pd.DataFrame(
        {
            "filename": filenames,
            "datetime": datetimes,
            "age_hours": age_hours,
            "age_days": age_days,
            "age_weeks": age_weeks,
            "age_months": age_months,
        }
    )
    return df


def get_hourly_files(df, KEEP_LAST_HOURS=config["KEEP_LAST_HOURS"]):
    df_hours = df.loc[df["age_hours"] <= KEEP_LAST_HOURS]
    hourly_files = df_hours.filename.tolist()
    return hourly_files


def get_daily_files(df, KEEP_LAST_DAYS=config["KEEP_LAST_DAYS"]):
    daily_files = []
    for i in range(KEEP_LAST_DAYS):
        day_df = df.loc[df["age_days"] == i]
        if len(day_df) > 0:
            daily_files.append(day_df.head(1)["filename"].values[0])
    return daily_files


def get_weekly_files(df, KEEP_LAST_WEEKS=config["KEEP_LAST_WEEKS"]):
    weekly_files = []
    for i in range(KEEP_LAST_WEEKS):
        day_df = df.loc[df["age_weeks"] == i]
        if len(day_df) > 0:
            weekly_files.append(day_df.head(1)["filename"].values[0])
    return weekly_files


def get_monthly_files(df, KEEP_LAST_MONTHS=config["KEEP_LAST_MONTHS"]):
    monthly_files = []
    for i in range(KEEP_LAST_MONTHS):
        day_df = df.loc[df["age_months"] == i]
        if len(day_df) > 0:
            monthly_files.append(day_df.head(1)["filename"].values[0])
    return monthly_files


def get_keep_file_list(
    filenames=list_files_in_folder_desc(),
    keep_last_hours=config["KEEP_LAST_HOURS"],
    keep_last_days=config["KEEP_LAST_DAYS"],
    keep_last_weeks=config["KEEP_LAST_WEEKS"],
    keep_last_months=config["KEEP_LAST_MONTHS"],
):
    df = get_file_info_dataframe(
        filenames=filenames,
        keep_last_hours=keep_last_hours,
        keep_last_days=keep_last_days,
        keep_last_weeks=keep_last_weeks,
        keep_last_months=keep_last_months,
    )

    hourly_files = get_hourly_files(df)
    daily_files = get_daily_files(df)
    weekly_files = get_weekly_files(df)
    monthly_files = get_monthly_files(df)

    keep_list = hourly_files + daily_files + weekly_files + monthly_files
    keep_list = list(set(keep_list))
    keep_list = sorted(keep_list, key=lambda x: x.split("_")[0], reverse=True)

    df["keep"] = df["filename"].apply(lambda x: True if x in keep_list else False)
    return keep_list


def run(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    database=config["POSTGRES_DB"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
):
    log.info("Running job...")
    filename = run_backup_job()

    if config["S3_UPLOAD"]:
        log.info("Uploading to Minio...")
        upload_file_to_s3_bucket(filename)

    log.info("Pruning old local files...")
    if config["KEEP_LOCAL_COPIES"]:
        prune_old_local_backup_files_except(get_keep_file_list(list_files_in_folder_desc()))
    else:
        prune_old_local_backup_files_except([])

    if config["S3_UPLOAD"]:
        log.info("Pruning old s3 files...")
        prune_old_s3_files_except(get_keep_file_list(list_files_in_s3_bucket_desc()))
    log.info("Job done!")


def main():
    log.info("timescaledb-backup starting up...")
    if config["MODE"] == "run_single_backup":
        run_backup_job()
        sys.exit()

    elif config["MODE"] == "restore_latest_local_file":
        restore_db_from_latest_file()
        sys.exit()

    elif config["MODE"] == "restore_latest_s3_file":
        download_latest_s3_file()
        restore_db_from_latest_file()
        sys.exit()

    elif config["MODE"].find("hourly") != -1:
        minutes = ":" + config["MODE"][-2:]
        log.info(f"hourly at {minutes}")
        schedule.every().hour.at(minutes).do(run)

    elif config["MODE"].find("daily") != -1:
        hours = config["MODE"][-5:-3]
        minutes = config["MODE"][-2:]
        tod = f"{hours}:{minutes}"
        log.info(f"daily at {tod}")
        schedule.every().day.at(tod).do(run)

    else:
        log.info("Wrong mode name, exiting...")
        exit()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
