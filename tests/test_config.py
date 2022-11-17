import json
from xnatuploader.workbook import load_config


def test_config(test_files):
    with open(test_files["basic"]["config"], "r") as fh:
        config_json = json.load(fh)
    config_excel = load_config(test_files["basic"]["config_excel"])
    assert config_json == config_excel
