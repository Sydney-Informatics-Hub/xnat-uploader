import xnatutils
import shutil
import json

from openpyxl import load_workbook

from pathlib import Path

from xnatuploader.xnatuploader import scan, upload
from xnatuploader.matcher import Matcher
from xnatuploader.workbook import new_workbook


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
    new_workbook(log_scanned)
    scan(matcher, Path(test_files["source"]), log_scanned)
    shutil.copy(log_scanned, log_uploaded)
    upload(xnat_session, matcher, project.name, log_uploaded, overwrite=True)
    scanned_wb = load_workbook(log_scanned)
    scanned_ws = scanned_wb["Files"]
    uploaded_wb = load_workbook(log_uploaded)
    uploaded_ws = uploaded_wb["Files"]
    uploads = {}
    for row in uploaded_ws.values:
        if row[0] != "Recipe":
            upload_row = matcher.from_spreadsheet(row)
            if upload_row.selected:
                uploads[upload_row.file] = upload_row
    expect = {}
    for row in scanned_ws.values:
        if row[0] != "Recipe":
            m = matcher.from_spreadsheet(row)
            if m.selected:
                subject = m.subject
                session = m.session
                if subject not in expect:
                    expect[subject] = {}
                if session not in expect[subject]:
                    expect[subject][session] = []
                expect[subject][session].append(m)
    for subject, sessions in expect.items():
        for session, rows in sessions.items():
            for row in rows:
                assert row.file in uploads
                assert uploads[row.file].status == "success"
            scans = xnatutils.ls(
                session,
                project_id=project.name,
                subject_id=subject,
                datatype="scan",
                connection=xnat_session,
            )
            assert scans is not None
            assert len(scans) == len(rows)
            for row in rows:
                assert row.dataset in scans
                del uploads[row.file]
    assert len(uploads) == 0


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
        SESSION_ID, project_id="Test001", datatype="session", connection=xnat_session
    )
    assert sessions is not None
    assert len(sessions) == 1
    session = sessions[0]
    assert session == SESSION_ID
    scans = xnatutils.ls(
        session,
        project_id="Test001",
        subject_id=SUBJECT_ID,
        datatype="scan",
        connection=xnat_session,
    )
    assert scans is not None
    assert len(scans) == 1
    assert scans[0] == DATASET_ID


def test_missing_file(xnat_project, tmp_path, test_files):
    xnat_session, project = xnat_project
    with open(test_files["config"], "r") as fh:
        config_json = json.load(fh)
        matcher = Matcher(config_json)
    log_scanned = tmp_path / "log_scanned.xlsx"
    log_uploaded = tmp_path / "log_uploaded.xlsx"
    new_workbook(log_scanned)
    scan(matcher, Path(test_files["source"]), log_scanned)
    scanned_wb = load_workbook(log_scanned)
    ws = scanned_wb["Files"]
    # change the third filename to trigger an error
    c = 0
    i = 0
    bad_file = None
    for row in ws.values:
        i += 1
        if row[0] != "Recipe":
            m = matcher.from_spreadsheet(row)
            if m.selected:
                c += 1
                if c == 3:
                    bad_file = ws.cell(i, 2).value + "broken"
                    ws.cell(i, 2).value = bad_file

    scanned_wb.save(log_uploaded)
    upload(xnat_session, matcher, project.name, log_uploaded, overwrite=True)
    uploads = {}
    uploaded_wb = load_workbook(log_uploaded)
    uploaded_ws = uploaded_wb["Files"]
    for row in uploaded_ws.values:
        if row[0] != "Recipe":
            upload_row = matcher.from_spreadsheet(row)
            if upload_row.selected:
                uploads[upload_row.file] = upload_row
                if upload_row.file == bad_file:
                    assert upload_row.status != "success"
                else:
                    assert upload_row.status == "success"
