from openpyxl import load_workbook
from pathlib import Path
import json

from matcher import Matcher
from xnatuploader import scan


FIXTURES_DIR = Path("tests") / "fixtures"
CONFIG = FIXTURES_DIR / "recipe-xnat.json"
SOURCE = FIXTURES_DIR / "source"
EXPECT_LOG = FIXTURES_DIR / "log.xlsx"


def assert_spreadsheets_equal(expect, got):
    es = expect.active
    gs = got.active
    grows = list(gs.values)
    for row in es.values:
        assert grows[0] == row
        grows = grows[1:]
    assert len(grows) == 0


def test_scan(tmp_path):
    with open(CONFIG, "r") as fh:
        config_json = json.load(fh)
        matcher = Matcher(config_json)
    log = tmp_path / "log.xlsx"
    scan(matcher, Path(SOURCE), log)
    expect_wb = load_workbook(EXPECT_LOG)
    got_wb = load_workbook(log)
    assert_spreadsheets_equal(expect_wb, got_wb)
