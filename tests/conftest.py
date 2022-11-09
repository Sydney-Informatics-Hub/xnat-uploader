import xnat4tests
import pytest
from pathlib import Path
from xnatuploader.matcher import Matcher


@pytest.fixture
def test_files():
    fixtures_dir = Path("tests") / "fixtures"
    return {
        "config_excel": fixtures_dir / "template.xlsx",
        "test_files": {
            "basic": {
                "dir": fixtures_dir / "basic",
                "config": fixtures_dir / "config_basic.json",
            },
            "bad_paths": {
                "dir": fixtures_dir / "bad_paths",
                "config": fixtures_dir / "config_bad_paths.json",
            },
        },
        "log": fixtures_dir / "scanned.xlsx",
    }


@pytest.fixture(scope="session")
def xnat_project():
    xnat4tests.launch_xnat()
    xnat = xnat4tests.connect()
    project = xnat.classes.ProjectData(parent=xnat, name="Test001")
    yield xnat, project
    # xnat4tests.stop_xnat()


@pytest.fixture(
    scope="module",
    params=[
        "basic",
        "one_glob",
        "multi_glob",
        "multi_glob_lookahead",
    ],
)
def matcher_case(request):
    MAPPINGS = {
        "Subject": ["ID"],
        "Session": ["DDDDDDDD"],
        "Dataset": ["Filename"],
    }
    CASES = {
        "basic": {
            "patterns": ["{SubjectName}-{ID}", "{DDDDDDDD}", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow-1234/20120301/test.dcm",
                    "values": {
                        "SubjectName": "JoeBlow",
                        "ID": "1234",
                        "DDDDDDDD": "20120301",
                        "Filename": "test.dcm",
                    },
                },
            ],
            "bad_paths": ["JoeBlow/201201/test.dcm", "bad"],
        },
        "one_glob": {
            "patterns": ["{SubjectName}-{ID}", "{DDDDDDDD}", "*", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow-1234/20120301/ignored/test.dcm",
                    "values": {
                        "SubjectName": "JoeBlow",
                        "ID": "1234",
                        "DDDDDDDD": "20120301",
                        "Filename": "test.dcm",
                    },
                }
            ],
            "bad_paths": [
                "JoeBlow-1234/20120301/test.dcm",
                "JoeBlow-1234/20120301/too/deep/test.dcm",
            ],
        },
        "multi_glob": {
            "patterns": ["{SubjectName}-{ID}", "{DDDDDDDD}", "**", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow-12345/20120301/ignoreMe/ignore_Me_too/test.dcm",
                    "values": {
                        "SubjectName": "JoeBlow",
                        "ID": "12345",
                        "DDDDDDDD": "20120301",
                        "Filename": "test.dcm",
                    },
                },
                {
                    "path": "JoeBlow-12345/20120301/ignoreOne/test.dcm",
                    "values": {
                        "SubjectName": "JoeBlow",
                        "ID": "12345",
                        "DDDDDDDD": "20120301",
                        "Filename": "test.dcm",
                    },
                },
            ],
            "bad_paths": [
                "JoeBlow-12345/20120301/test.dcm",
            ],
        },
        "multi_glob_lookahead": {
            "patterns": ["{SubjectName}-{ID}", "**", "{DDDDDDDD}", "{Filename}"],
            "paths": [
                {
                    "path": "JoeBlow-12345/ignoreMe/ignore_Me_too/20120301/test.dcm",
                    "values": {
                        "SubjectName": "JoeBlow",
                        "ID": "12345",
                        "DDDDDDDD": "20120301",
                        "Filename": "test.dcm",
                    },
                },
                {
                    "path": "JoeBlow-12345/ignoreOne/20120301/test.dcm",
                    "values": {
                        "SubjectName": "JoeBlow",
                        "ID": "12345",
                        "DDDDDDDD": "20120301",
                        "Filename": "test.dcm",
                    },
                },
            ],
            "bad_paths": [
                "JoeBlow-12345/20120301/test.dcm",
            ],
        },
    }
    case = CASES[request.param]
    matcher = Matcher({"paths": {"test": case["patterns"]}, "mappings": MAPPINGS})
    return matcher, case
