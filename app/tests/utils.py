from pathlib import Path

from app import main
from app.tests import test_data, utils


def copy_fake_db_files_to_backup_directory():
    for filename in test_data.filenames:
        f = open(f"./{main.config['BACKUP_FOLDER']}/{filename}", "w")
        f.close()


def delete_all_files_from_backup_folder():
    for f in Path(f'./{main.config["BACKUP_FOLDER"]}').glob("*"):
        f.unlink()


def test_delete_all_files_from_backup_folder():
    utils.delete_all_files_from_backup_folder()
    assert len(list(Path(f'./{main.config["BACKUP_FOLDER"]}').glob("*"))) == 0
    copy_fake_db_files_to_backup_directory()
    assert len(list(Path(f'./{main.config["BACKUP_FOLDER"]}').glob("*"))) == 15
    utils.delete_all_files_from_backup_folder()
