import time
from importlib import reload

import pytest

from app import main
from app.tests import pg_utils, utils


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    reload(main)
    reload(pg_utils)


def test_run_backup_job():
    pg_utils.insert_demo_data()
    assert main.get_timescale_version() == "2.1.0"

    utils.delete_all_files_from_backup_folder()

    for _ in range(2):
        main.run()
        time.sleep(1)

    main.delete_db()
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
            cur.execute(
                """
                DROP TABLE test_table;
                """
            )
    utils.delete_all_files_from_backup_folder()


def test_run_backup_job_db_exists(monkeypatch):
    with pytest.raises(FileExistsError):
        main.run()
        main.restore_db_from_latest_file()
