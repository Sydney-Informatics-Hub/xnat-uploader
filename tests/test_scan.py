import logging
from openpyxl import load_workbook
from pathlib import Path

from xnatuploader.matcher import Matcher
from xnatuploader.xnatuploader import scan, collate_uploads
from xnatuploader.workbook import load_config, new_workbook

logger = logging.getLogger(__name__)


def assert_worksheets_equal(expect, got):
    grows = list(got.values)
    for row in expect.values:
        assert grows[0] == row
        grows = grows[1:]
    assert len(grows) == 0


def test_scan(tmp_path, test_files):
    fileset = test_files["basic"]
    config = load_config(fileset["config_excel"])
    matcher = Matcher(config)
    log = tmp_path / "log.xlsx"
    new_workbook(log)
    scan(matcher, Path(fileset["dir"]), log)
    expect_wb = load_workbook(fileset["scanned_excel"])
    got_wb = load_workbook(log)
    assert "Files" in got_wb
    assert_worksheets_equal(expect_wb["Files"], got_wb["Files"])


def test_collation(tmp_path, test_files, uploads_dict):
    fileset = test_files["basic"]
    config = load_config(fileset["config_excel"])
    matcher = Matcher(config)
    log = tmp_path / "log.xlsx"
    new_workbook(log)
    scan(matcher, Path(fileset["dir"]), log)
    project_id = uploads_dict["project"]
    wb = load_workbook(log)
    ws = wb["Files"]
    header = True
    files = []
    for row in ws.values:
        if header:
            header = False
        else:
            matchfile = matcher.from_spreadsheet(row)
            files.append(matchfile)

    uploads = collate_uploads(project_id, files)
    for session_scan, upload in uploads.items():
        uploads[session_scan] = [f.file for f in uploads[session_scan].files]
    assert uploads == uploads_dict["uploads"]
