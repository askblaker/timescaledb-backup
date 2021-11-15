import os
import time
from importlib import reload

import psycopg2
import pytest
import schedule

from app import main
from app.tests import test_data, utils


def test_database_exists_wrong_input(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "non_existing")
    reload(main)
    with pytest.raises(SystemExit):
        main.database_exists()
    monkeypatch.delenv("POSTGRES_HOST")
    reload(main)


def test_prune_local_backup_files():
    utils.delete_all_files_from_backup_folder()
    utils.copy_fake_db_files_to_backup_directory()
    assert set(os.listdir("./backups")) == set(test_data.filenames)
    keep_list = main.get_keep_file_list(test_data.filenames)
    main.prune_old_local_backup_files_except(keep_list)
    assert set(os.listdir("./backups")) == set(keep_list)
    main.prune_old_local_backup_files_except([])
    assert "deleted" == "deleted"


def test_main(monkeypatch):
    def mock_run_backup_job():
        pass

    def mock_run_pending():
        return mock_run()

    def mock_run():
        pass

    def mock_sleep(num):
        exit()

    monkeypatch.setattr(main, "run_backup_job", mock_run_backup_job)
    monkeypatch.setattr(main, "run", mock_run)
    monkeypatch.setattr(time, "sleep", mock_sleep)
    monkeypatch.setattr(schedule, "run_pending", mock_run_pending)

    assert main.config["MODE"] == "hourly_00"

    with pytest.raises(SystemExit):
        main.main()

    monkeypatch.setitem(main.config, "MODE", "once")
    with pytest.raises(SystemExit):
        main.main()

    monkeypatch.setitem(main.config, "MODE", "daily_11_53")
    with pytest.raises(SystemExit):
        main.main()


def test_list_non_existing_directory():
    with pytest.raises(FileNotFoundError):
        main.list_files_in_folder_desc("nonexisting_folder")


def test_get_psycopg2_conn_wrong_input(caplog):
    with pytest.raises(psycopg2.OperationalError):
        main.get_psycopg2_conn(host="nonexisting_host", port=1234)


def test_get_timescale_version_on_vanilla_postgres():
    assert main.get_timescale_version(host="postgres_12") is None


def test_restore_db_from_latest_file_no_folder():
    utils.delete_all_files_from_backup_folder()
    with pytest.raises(FileNotFoundError):
        main.restore_db_from_latest_file()


def test_run_with_local_storage_deactivated(monkeypatch):
    monkeypatch.setenv("KEEP_LOCAL_COPIES", "false")
    reload(main)
    assert main.config["KEEP_LOCAL_COPIES"] is False
    main.run()
