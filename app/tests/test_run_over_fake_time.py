import datetime

from freezegun import freeze_time

from app import main
from app.tests import utils


def copy_fake_file_to_backup_directory_from_time_string(time_string):
    timestr = main.get_time_string()
    database = "testingdb"
    pg_major_version = "12"
    timescale_version = "1.2.3"
    filename = f"{timestr}_DB-{database}_PG-{pg_major_version}_TS-{timescale_version}.bak"
    f = open(f"./{main.config['BACKUP_FOLDER']}/{filename}", "w")
    f.close()


def test_run_for_a_year_daily():
    initial_datetime = datetime.datetime(year=2021, month=1, day=1, hour=15, minute=30, second=00)
    with freeze_time(initial_datetime) as frozen_datetime:
        for _ in range(366):
            time_string = main.get_time_string()
            copy_fake_file_to_backup_directory_from_time_string(time_string)
            main.prune_old_local_backup_files_except(main.get_keep_file_list(main.list_files_in_folder_desc()))
            frozen_datetime.tick(delta=datetime.timedelta(days=1))

        expected_result = [
            "20220101153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211231153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211230153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211229153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211228153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211227153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211226153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211219153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211212153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211130153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20211031153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210930153000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210831153000_DB-testingdb_PG-12_TS-1.2.3.bak",
        ]

        assert main.list_files_in_folder_desc() == expected_result
        utils.delete_all_files_from_backup_folder()


def test_run_for_two_months_hourly():
    initial_datetime = datetime.datetime(year=2021, month=1, day=1, hour=15, minute=30, second=00)
    with freeze_time(initial_datetime) as frozen_datetime:
        for _ in range(61):
            for _ in range(24):
                time_string = main.get_time_string()
                copy_fake_file_to_backup_directory_from_time_string(time_string)
                main.prune_old_local_backup_files_except(main.get_keep_file_list(main.list_files_in_folder_desc()))
                frozen_datetime.tick(delta=datetime.timedelta(hours=1))

        expected_result = [
            "20210303143000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210303133000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210303123000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210303113000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210303103000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210303093000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210303083000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210302233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210301233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210228233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210227233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210226233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210225233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210221233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210214233000_DB-testingdb_PG-12_TS-1.2.3.bak",
            "20210131233000_DB-testingdb_PG-12_TS-1.2.3.bak",
        ]
        assert main.list_files_in_folder_desc() == expected_result
        utils.delete_all_files_from_backup_folder()
