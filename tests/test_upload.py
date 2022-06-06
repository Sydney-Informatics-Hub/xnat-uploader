import pytest
import xnatutils
import shutil
import json

from openpyxl import load_workbook

from pathlib import Path

from xnatuploader import upload
from matcher import Matcher

from .utils import assert_spreadsheets_equal


FIXTURES_DIR = Path("tests/fixtures")
DICOM = FIXTURES_DIR / "sample_dicoms" / "image-00000.dcm"
SESSION_ID = "SESSION01"
DATASET_ID = "DATASET01"
SUBJECT_ID = "1234-5678"
# XNAT : Project / Subject / Session


def test_upload_from_spreadsheet(xnat_project, tmp_path, test_files):
    xnat_session, project = xnat_project
    with open(test_files["config"], "r") as fh:
        config_json = json.load(fh)
        matcher = Matcher(config_json)
    log = tmp_path / "log.xlsx"
    shutil.copy(test_files["log"], log)
    upload(xnat_session, matcher, project, log)
    expect_wb = load_workbook(test_files["log"])
    got_wb = load_workbook(log)
    assert_spreadsheets_equal(expect_wb, got_wb)


@pytest.mark.skip(reason="incomplete")
def test_upload_one(xnat_project, tmp_path):
    xnat_session, project = xnat_project
    subject = xnat_session.classes.SubjectData(parent=project, label=SUBJECT_ID)
    assert subject is not None
    xnatutils.put(
        SESSION_ID,
        DATASET_ID,
        [str(DICOM)],
        project_id=project.name,
        subject_id=SUBJECT_ID,
        create_session=True,
        connection=xnat_session,
    )
    sessions = xnatutils.ls(
        project_id="Test001", datatype="session", connection=xnat_session
    )
    assert sessions is not None
    assert len(sessions) == 1
    session = sessions[0]
    assert session == SESSION_ID
    scans = xnatutils.ls(xnat_id=session, datatype="scan", connection=xnat_session)
    assert scans is not None
    assert len(scans) == 1
    xnatutils.get(
        SESSION_ID,
        tmp_path,
        project_id=project.name,
        subject_id=SUBJECT_ID,
        connection=xnat_session,
    )
