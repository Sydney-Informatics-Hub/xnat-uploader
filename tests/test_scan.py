from openpyxl import load_workbook
from pathlib import Path

from xnatuploader.matcher import Matcher
from xnatuploader.xnatuploader import scan
from xnatuploader.workbook import load_config

from .utils import assert_spreadsheets_equal


def test_scan(tmp_path, test_files):
    config_json = load_config(test_files["config_excel"])
    matcher = Matcher(config_json)
    log = tmp_path / "log.xlsx"
    scan(matcher, Path(test_files["source"]), log)
    expect_wb = load_workbook(test_files["log"])
    got_wb = load_workbook(log)
    assert_spreadsheets_equal(expect_wb, got_wb)
