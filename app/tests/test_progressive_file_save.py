import os
from importlib import reload

from freezegun import freeze_time

from app import main
from app.tests import utils
from app.tests.test_data import filenames


@freeze_time("2021-03-27 06:38:45")
def test_get_hourly_file_list():
    df = main.get_file_info_dataframe(filenames)
    hourly_files = main.get_hourly_files(df, 3)
    expected_hourly_files = [
        "20210327053800_DB-mydb_PG-12.6_TS-None.bak",
        "20210327043801_DB-mydb_PG-12.6_TS-None.bak",
        "20210327033802_DB-mydb_PG-12.6_TS-None.bak",
    ]
    assert hourly_files == expected_hourly_files


def test_get_hourly_now():
    utils.delete_all_files_from_backup_folder()
    filename = main.run_backup_job()
    directory_list = list(os.listdir(f"./{main.config['BACKUP_FOLDER']}"))
    assert len(directory_list) == 1
    assert directory_list[0] == filename

    keep_files = main.get_keep_file_list([filename])
    main.prune_old_local_backup_files_except(keep_files)
    directory_list = list(os.listdir(f"./{main.config['BACKUP_FOLDER']}"))
    assert len(directory_list) == 1
    assert directory_list[0] == filename
    utils.delete_all_files_from_backup_folder()


@freeze_time("2021-03-27 06:38:45")
def test_get_daily_file_list():
    df = main.get_file_info_dataframe(filenames)
    daily_files = main.get_daily_files(df, 3)
    expected_daily_files = [
        "20210327053800_DB-mydb_PG-12.6_TS-None.bak",
        "20210326233806_DB-mydb_PG-12.6_TS-None.bak",
        "20210325223808_DB-mydb_PG-12.6_TS-None.bak",
    ]
    assert daily_files == expected_daily_files


@freeze_time("2021-03-27 06:38:45")
def test_get_weekly_file_list():
    df = main.get_file_info_dataframe(filenames)
    weekly_files = main.get_weekly_files(df, 3)
    expected_weekly_files = [
        "20210327053800_DB-mydb_PG-12.6_TS-None.bak",
        "20210321053809_DB-mydb_PG-12.6_TS-None.bak",
    ]
    assert weekly_files == expected_weekly_files


@freeze_time("2021-03-27 06:38:45")
def test_get_monthly_file_list():
    df = main.get_file_info_dataframe(filenames)
    monthly_files = main.get_monthly_files(df, 3)
    expected_monthly_files = [
        "20210327053800_DB-mydb_PG-12.6_TS-None.bak",
        "20210227053810_DB-mydb_PG-12.6_TS-None.bak",
        "20210126053812_DB-mydb_PG-12.6_TS-None.bak",
    ]
    assert monthly_files == expected_monthly_files


@freeze_time("2021-03-27 06:38:45")
def test_get_keep_file_list2(monkeypatch):
    monkeypatch.setenv("KEEP_LAST_HOURS", "3")
    monkeypatch.setenv("KEEP_LAST_DAYS", "3")
    monkeypatch.setenv("KEEP_LAST_WEEKS", "3")
    monkeypatch.setenv("KEEP_LAST_MONTHS", "3")
    reload(main)

    df = main.get_file_info_dataframe(filenames)
    keep_hourly = main.get_hourly_files(df)
    keep_daily = main.get_daily_files(df)
    keep_weekly = main.get_weekly_files(df)
    keep_monthly = main.get_monthly_files(df)

    unsorted = keep_hourly + keep_daily + keep_weekly + keep_monthly
    unsorted = list(set(unsorted))
    expected_result = sorted(unsorted, key=lambda x: x.split("_")[0], reverse=True)

    keep_files = main.get_keep_file_list(filenames)
    assert keep_files == expected_result

    monkeypatch.delenv("KEEP_LAST_HOURS")
    monkeypatch.delenv("KEEP_LAST_DAYS")
    monkeypatch.delenv("KEEP_LAST_WEEKS")
    monkeypatch.delenv("KEEP_LAST_MONTHS")
    reload(main)
