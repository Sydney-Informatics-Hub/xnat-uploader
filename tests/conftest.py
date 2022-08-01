import xnat4tests
import pytest
from pathlib import Path
from xnatuploader.matcher import Matcher


@pytest.fixture
def test_files():
    fixtures_dir = Path("tests") / "fixtures"
    return {
        "config_excel": fixtures_dir / "template.xlsx",
        "config": fixtures_dir / "recipe-xnat.json",
        "source": fixtures_dir / "source",
        "log": fixtures_dir / "scanned.xlsx",
    }


@pytest.fixture(scope="session")
def xnat_project():
    xnat4tests.launch_xnat()
    xnat = xnat4tests.connect()
    project = xnat.classes.ProjectData(parent=xnat, name="Test001")
    yield xnat, project
    xnat4tests.stop_xnat()


@pytest.fixture(scope="module", params=["basic", "one_glob", "multi_glob"])
def matcher_case(request):
    MAPPINGS = {
        "Subject": ["Subject"],
        "Session": ["YYYY", "MM", "DD"],
        "Dataset": ["Filename"],
    }
    CASES = {
        "basic": {
            "patterns": ["{Subject}", "{YYYY}{MM}{DD}", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow/20120301/test.dcm",
                    "values": {
                        "Subject": "JoeBlow",
                        "Session": "20120301",
                        "Dataset": "test.dcm",
                    },
                },
            ],
            "bad_paths": ["JoeBlow/201201/test.dcm", "bad"],
        },
        "one_glob": {
            "patterns": ["{Subject}", "{YYYY}{MM}{DD}", "*", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow/20120301/ignored/test.dcm",
                    "values": {
                        "Subject": "JoeBlow",
                        "Session": "20120301",
                        "Dataset": "test.dcm",
                    },
                }
            ],
            "bad_paths": [
                "JoeBlow/20120301/test.dcm",
                "JoeBlow/20120301/too/deep/test.dcm",
            ],
        },
        "multi_glob": {
            "patterns": ["{Subject}", "{YYYY}{MM}{DD}", "**", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow/20120301/ignoreMe/ignore_Me_too/test.dcm",
                    "values": {
                        "Subject": "JoeBlow",
                        "Session": "20120301",
                        "Dataset": "test.dcm",
                    },
                },
                {
                    "path": "JoeBlow/20120301/test.dcm",
                    "values": {
                        "Subject": "JoeBlow",
                        "Session": "20120301",
                        "Dataset": "test.dcm",
                    },
                },
            ],
            "bad_paths": [
                "JoeBlow/201201/test.dcm",
            ],
        },
    }
    case = CASES[request.param]
    matcher = Matcher({"paths": {"test": case["patterns"]}, "mappings": MAPPINGS})
    return matcher, case
