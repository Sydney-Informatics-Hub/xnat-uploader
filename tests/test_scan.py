from openpyxl import load_workbook
from pathlib import Path

from xnatuploader.matcher import Matcher
from xnatuploader.xnatuploader import scan
from xnatuploader.workbook import load_config, new_workbook


def assert_worksheets_equal(expect, got):
    grows = list(got.values)
    for row in expect.values:
        assert grows[0] == row
        grows = grows[1:]
    assert len(grows) == 0


def test_scan(tmp_path, test_files):
    config_json = load_config(test_files["config_excel"])
    matcher = Matcher(config_json)
    log = tmp_path / "log.xlsx"
    new_workbook(log)
    scan(matcher, Path(test_files["source"]), log)
    expect_wb = load_workbook(test_files["log"])
    got_wb = load_workbook(log)
    assert "Files" in got_wb
    assert_worksheets_equal(expect_wb["Files"], got_wb["Files"])
