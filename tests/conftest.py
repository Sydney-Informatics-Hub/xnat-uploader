import xnat4tests
import pytest
from pathlib import Path
from xnatuploader.matcher import Matcher


@pytest.fixture
def test_files():
    fixtures_dir = Path("tests") / "fixtures"
    return {
        "basic": {
            "dir": fixtures_dir / "basic",
            "config": fixtures_dir / "config_basic.json",
            "config_excel": fixtures_dir / "basic_init.xlsx",
            "scanned_excel": fixtures_dir / "basic_scanned.xlsx",
        },
        "bad_paths": {
            "dir": fixtures_dir / "bad_paths",
            "config": fixtures_dir / "config_bad_paths.json",
        },
        "sanitization": {
            "dir": fixtures_dir / "sanitization",
            "config": fixtures_dir / "config_bad_paths.json",
        },
    }


@pytest.fixture
def uploads_dict():
    source_dir = Path("tests") / "fixtures/basic"
    return {
        "project": "Project",
        "uploads": {
            "002304_CT1:Head_CT": [
                str(
                    source_dir
                    / "DOE^JOHN-002304/20200312HeadCT/Head CT/image-00000.dcm"
                ),
                str(
                    source_dir
                    / "DOE^JOHN-002304/20200312HeadCT/Head CT/image-00001.dcm"
                ),
            ],
            "002304_CT1:Neck_CT": [
                str(
                    source_dir
                    / "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00000.dcm"
                ),
                str(
                    source_dir
                    / "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00001.dcm"
                ),
                str(
                    source_dir
                    / "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00002.dcm"
                ),
            ],
            "397829_CT1:SomeCT": [
                str(source_dir / "ROE^JANE-397829/20190115/SomeCT/img-00000.dcm"),
            ],
            "397829_CT2:SomeCT": [
                str(source_dir / "ROE^JANE-397829/20200623/SomeCT/img-00000.dcm"),
            ],
            "397829_CT3:SomeCT": [
                str(source_dir / "ROE^JANE-397829/20210414/SomeCT/image-00000.dcm"),
            ],
            "038945_CT1:X_Rays": [
                str(source_dir / "Smith^John-038945/20200303/X-Rays/img-00000.dcm"),
            ],
        },
    }


@pytest.fixture
def sanitized_dict():
    source_dir = Path("tests") / "fixtures/sanitization"
    return {
        "project": "Project",
        "uploads": {
            "99999_CT1:foo_bar": [
                str(source_dir / "johndoe-99999/20221122/foo(bar/image-00000.dcm"),
            ],
            "99999_CT1:foo_bar2": [
                str(source_dir / "johndoe-99999/20221122/foo,bar/image-00000.dcm"),
            ],
            "99999_CT1:foo_bar3": [
                str(source_dir / "johndoe-99999/20221122/foo_bar/image-00000.dcm"),
            ],
        },
    }


@pytest.fixture(scope="session")
def xnat_connection():
    xnat4tests.launch_xnat()
    xnat = xnat4tests.connect()
    yield xnat
    xnat4tests.stop_xnat()


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
