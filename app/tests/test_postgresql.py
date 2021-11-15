import time
from importlib import reload

import pytest

from app import main
from app.tests import pg_utils, utils


def test_run_backup_job_pg12(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "postgres_12")
    monkeypatch.setenv("TIMESCALE", "false")
    reload(main)
    reload(pg_utils)

    pg_utils.insert_demo_data()
    assert main.get_timescale_version() is None

    utils.delete_all_files_from_backup_folder()

    for _ in range(2):
        main.run()
        time.sleep(1)

    main.delete_db(pg_version="12")
    main.restore_db_from_latest_file()

    with main.get_psycopg2_conn() as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM test_table;
                """
            )
            result = cur.fetchone()
            assert result == (1, 2)
    pg_utils.delete_demo_data()
    utils.delete_all_files_from_backup_folder()


def test_run_backup_job_pg13(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "postgres_13")
    monkeypatch.setenv("TIMESCALE", "false")
    reload(main)
    reload(pg_utils)

    pg_utils.insert_demo_data()
    assert main.get_timescale_version() is None

    utils.delete_all_files_from_backup_folder()

    for _ in range(2):
        main.run()
        time.sleep(1)

    main.delete_db(pg_version="12")
    main.restore_db_from_latest_file()

    with main.get_psycopg2_conn() as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM test_table;
                """
            )
            result = cur.fetchone()
            assert result == (1, 2)
    pg_utils.delete_demo_data()
    utils.delete_all_files_from_backup_folder()


def test_restore_db_no_suitable_file_found():
    utils.delete_all_files_from_backup_folder()
    f = open(f"./{main.config['BACKUP_FOLDER']}/weird_non_standard_name", "w")
    f.close()
    with pytest.raises(FileNotFoundError):
        main.restore_db_from_latest_file()
    utils.delete_all_files_from_backup_folder()


def test_restore_existing_db():
    with pytest.raises(FileExistsError):
        main.run_backup_job()
        time.sleep(1)
        main.restore_db_from_latest_file()
    utils.delete_all_files_from_backup_folder()


def test_restore_with_overwrite(monkeypatch):
    monkeypatch.setenv("RESTORE_OVERWRITE", "true")
    reload(main)
    main.run_backup_job()
    time.sleep(1)
    main.restore_db_from_latest_file()
    utils.delete_all_files_from_backup_folder()
