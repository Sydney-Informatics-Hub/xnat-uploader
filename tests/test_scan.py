from openpyxl import load_workbook
from pathlib import Path
import json

from xnatuploader.matcher import Matcher
from xnatuploader.xnatuploader import scan

from .utils import assert_spreadsheets_equal


def test_scan(tmp_path, test_files):
    with open(test_files["config"], "r") as fh:
        config_json = json.load(fh)
        matcher = Matcher(config_json)
    log = tmp_path / "log.xlsx"
    scan(matcher, Path(test_files["source"]), log)
    expect_wb = load_workbook(test_files["log"])
    got_wb = load_workbook(log)
    assert_spreadsheets_equal(expect_wb, got_wb)
