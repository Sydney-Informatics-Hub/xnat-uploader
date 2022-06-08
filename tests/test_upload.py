import pytest
import xnatutils
import shutil
import json

from openpyxl import load_workbook

from pathlib import Path

from xnatuploader import scan, upload
from matcher import Matcher

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
    log_scanned = tmp_path / "log_scanned.xlsx"
    log_uploaded = tmp_path / "log_uploaded.xlsx"
    scan(matcher, Path(test_files["source"]), log_scanned)
    shutil.copy(log_scanned, log_uploaded)
    upload(xnat_session, matcher, project.name, log_uploaded)
    scanned_wb = load_workbook(log_scanned)
    scanned_ws = scanned_wb.active
    uploaded_wb = load_workbook(log_uploaded)
    uploaded_ws = uploaded_wb.active
    uploads = {}
    for row in uploaded_ws.values:
        if row[0] != "Recipe":
            upload_row = matcher.from_spreadsheet(row)
            if upload_row.selected:
                uploads[upload_row.file] = upload_row
    for row in scanned_ws.values:
        if row[0] != "Recipe":
            scanned_row = matcher.from_spreadsheet(row)
            if scanned_row.selected:
                assert scanned_row.file in uploads
                assert uploads[scanned_row.file].status == "success"
                from_ls = xnatutils.ls(
                    project_id=project.name,
                    subject_id=scanned_row.subject,
                    datatype="session",
                    connection=xnat_session,
                )
                assert from_ls is not None
                print(from_ls)
                del uploads[scanned_row.file]
    assert len(uploads) == 0


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
