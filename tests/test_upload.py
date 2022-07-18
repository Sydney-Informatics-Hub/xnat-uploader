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


def test_upload_from_spreadsheet(xnat_project, tmp_path, test_files):
    xnat_session, project = xnat_project
    with open(test_files["config"], "r") as fh:
        config_json = json.load(fh)
        matcher = Matcher(config_json)
    log_scanned = tmp_path / "log_scanned.xlsx"
    log_uploaded = tmp_path / "log_uploaded.xlsx"
    downloads = tmp_path / "downloads"
    new_workbook(log_scanned)
    scan(matcher, Path(test_files["source"]), log_scanned)
    shutil.copy(log_scanned, log_uploaded)
    upload(xnat_session, matcher, project.name, log_uploaded, overwrite=True)
    # scanned_wb = load_workbook(log_scanned)
    # scanned_ws = scanned_wb["Files"]
    uploaded_wb = load_workbook(log_uploaded)
    uploaded_ws = uploaded_wb["Files"]
    uploads = {}
    for row in uploaded_ws.values:
        if row[0] != "Recipe":
            upload_row = matcher.from_spreadsheet(row)
            if upload_row.selected:
                uploads[upload_row.file] = upload_row
    expect = {}
    # Originally was using scanned_ws for this, but that doesn't have
    # session labels. A more honest test would recreate them or get them
    # from the upload spreadsheet.
    for row in uploaded_ws.values:
        if row[0] != "Recipe":
            m = matcher.from_spreadsheet(row)
            if m.selected:
                subject = m.subject
                session_label = m.session_label
                assert session_label is not None
                if subject not in expect:
                    expect[subject] = {}
                if session_label not in expect[subject]:
                    expect[subject][session_label] = []
                expect[subject][session_label].append(m)
    for subject, sessions in expect.items():
        for session_label, rows in sessions.items():
            for row in rows:
                assert row.file in uploads
                assert uploads[row.file].status == "success"
            xnatutils.get(
                session_label,
                downloads,
                project_id=project.name,
                connection=xnat_session,
            )
            if session_label is not None:
                downloaded = get_downloaded(downloads / session_label)
                assert len(downloaded) == len(rows)
                for row in rows:
                    assert Path(row.file).name in downloaded
                    del uploads[row.file]
    assert len(uploads) == 0


def get_downloaded(session_download):
    files = []
    for child in session_download.iterdir():
        if child.is_dir():
            for file in child.iterdir():
                if file.is_file() and file.suffix == ".dcm":
                    files.append(file.name)
    return files


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
