import time
from importlib import reload

import pytest

from app import main
from app.tests import test_data, utils


def test_download_latest_s3_file(monkeypatch):
    monkeypatch.setenv("S3_UPLOAD", "true")
    reload(main)
    assert len(main.list_files_in_folder_desc()) == 0
    for _ in range(3):
        main.run()
        time.sleep(1)
    assert len(main.list_files_in_folder_desc()) == 3
    utils.delete_all_files_from_backup_folder()
    assert len(main.list_files_in_folder_desc()) == 0
    main.download_latest_s3_file()
    assert len(main.list_files_in_folder_desc()) == 1


def test_s3_prune_nonexisting_bucket(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "very_non_existing")
    reload(main)

    with pytest.raises(SystemExit):
        main.prune_old_s3_files_except([])

    monkeypatch.delenv("S3_BUCKET", raising=False)
    reload(main)


def test_s3_functions_bucket(monkeypatch):
    monkeypatch.setenv("S3_UPLOAD", "true")
    reload(main)
    utils.delete_all_files_from_backup_folder()
    main.prune_old_s3_files_except([])

    utils.copy_fake_db_files_to_backup_directory()
    for filename in test_data.filenames:
        main.upload_file_to_s3_bucket(filename)
    assert main.list_files_in_s3_bucket_desc() == test_data.filenames

    main.prune_old_s3_files_except([])
    assert main.list_files_in_s3_bucket_desc() == []

    utils.copy_fake_db_files_to_backup_directory()
    for filename in test_data.filenames:
        main.upload_file_to_s3_bucket(filename)
    assert main.list_files_in_s3_bucket_desc() == test_data.filenames

    main.prune_old_s3_files_except(main.get_keep_file_list(main.list_files_in_s3_bucket_desc()))

    keep_files = main.get_keep_file_list(test_data.filenames)
    assert main.list_files_in_s3_bucket_desc() == keep_files
    utils.delete_all_files_from_backup_folder()
    monkeypatch.delenv("S3_UPLOAD")
