from openpyxl import load_workbook
from pathlib import Path
from xnatuploader import load_recipes, scan_files

RECIPE = "fixtures/recipe-example.json"
SOURCE = "fixtures/source"
LOG = "fixtures/log.xlsx"
LOG2 = "fixtures/my_log.xlsx"


def assert_spreadsheets_equal(expect, got):
    es = expect.active
    gs = got.active
    grows = list(gs.values)
    for row in es.values:
        assert grows[0] == row
        grows = grows[1:]
    assert len(grows) == 0


def test_scan(tmp_path):
    params, recipes = load_recipes(RECIPE)
    log = tmp_path / "log.xlsx"
    scan_files(params, recipes, Path(SOURCE), log)
    expect_wb = load_workbook(LOG)
    got_wb = load_workbook(log)
    assert_spreadsheets_equal(expect_wb, got_wb)
