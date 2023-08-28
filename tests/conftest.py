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
            "strict_scan_ids": False,
            "uploads_dict": uploads_dict(False),
        },
        "basic_strict": {
            "dir": fixtures_dir / "basic",
            "config": fixtures_dir / "config_basic.json",
            "config_excel": fixtures_dir / "basic_init.xlsx",
            "scanned_excel": fixtures_dir / "basic_scanned_scan_ids.xlsx",
            "strict_scan_ids": True,
            "uploads_dict": uploads_dict(True),
        },
        "bad_paths": {
            "dir": fixtures_dir / "bad_paths",
            "config": fixtures_dir / "config_basic.json",
        },
        "secret_pdf": {
            "dir": fixtures_dir / "secret_pdf",
            "config_excel": fixtures_dir / "basic_init.xlsx",
            "scanned_excel": fixtures_dir / "secret_pdf_scanned.xlsx",
        },
        "sanitisation": {
            "dir": fixtures_dir / "sanitisation",
            "config": fixtures_dir / "config_basic.json",
        },
    }


@pytest.fixture
def uploads_dict_fixture():
    source_dir = Path("tests") / "fixtures/basic"
    return {
        "project": "Project",
        "skipped": 7,
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


def uploads_dict(strict_scan_ids=False):
    source_dir = Path("tests") / "fixtures/basic"
    BASE_UPLOADS = {
        "002304_CT1:Head_CT": {
            "scan_id": "3",
            "files": [
                "DOE^JOHN-002304/20200312HeadCT/Head CT/image-00000.dcm",
                "DOE^JOHN-002304/20200312HeadCT/Head CT/image-00001.dcm",
            ],
        },
        "002304_CT1:Neck_CT": {
            "scan_id": "6168",
            "files": [
                "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00000.dcm",
                "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00001.dcm",
                "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00002.dcm",
            ],
        },
        "397829_CT1:SomeCT": {
            "scan_id": "6168",
            "files": ["ROE^JANE-397829/20190115/SomeCT/img-00000.dcm"],
        },
        "397829_CT2:SomeCT": {
            "scan_id": "6168",
            "files": ["ROE^JANE-397829/20200623/SomeCT/img-00000.dcm"],
        },
        "397829_CT3:SomeCT": {
            "scan_id": "6168",
            "files": ["ROE^JANE-397829/20210414/SomeCT/image-00000.dcm"],
        },
        "038945_CT1:X_Rays": {
            "scan_id": "6168",
            "files": ["Smith^John-038945/20200303/X-Rays/img-00000.dcm"],
        },
    }

    uploads = {}
    for session_label, details in BASE_UPLOADS.items():
        use_label = session_label
        if strict_scan_ids:
            parts = session_label.split(":")
            use_label = parts[0] + "_" + details["scan_id"] + ":" + parts[1]
        uploads[use_label] = [str(source_dir / f) for f in details["files"]]
    return {"project": "Project", "skipped": 7, "uploads": uploads}

    #     "uploads": {
    #         "002304_CT1:Head_CT": [
    #             str(
    #                 source_dir
    #                 / "DOE^JOHN-002304/20200312HeadCT/Head CT/image-00000.dcm"
    #             ),
    #             str(
    #                 source_dir
    #                 / "DOE^JOHN-002304/20200312HeadCT/Head CT/image-00001.dcm"
    #             ),
    #         ],
    #         "002304_CT1:Neck_CT": [
    #             str(
    #                 source_dir
    #                 / "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00000.dcm"
    #             ),
    #             str(
    #                 source_dir
    #                 / "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00001.dcm"
    #             ),
    #             str(
    #                 source_dir
    #                 / "DOE^JOHN-002304/20200312HeadCT/Neck CT/image-00002.dcm"
    #             ),
    #         ],
    #         "397829_CT1:SomeCT": [
    #             str(source_dir / "ROE^JANE-397829/20190115/SomeCT/img-00000.dcm"),
    #         ],
    #         "397829_CT2:SomeCT": [
    #             str(source_dir / "ROE^JANE-397829/20200623/SomeCT/img-00000.dcm"),
    #         ],
    #         "397829_CT3:SomeCT": [
    #             str(source_dir / "ROE^JANE-397829/20210414/SomeCT/image-00000.dcm"),
    #         ],
    #         "038945_CT1:X_Rays": [
    #             str(source_dir / "Smith^John-038945/20200303/X-Rays/img-00000.dcm"),
    #         ],
    #     },
    # }


@pytest.fixture
def sanitised_dict():
    source_dir = Path("tests") / "fixtures/sanitisation"
    return {
        "project": "Project",
        "skipped": 0,
        "uploads": {
            "99999_CT1_6168:foo_bar": [
                str(source_dir / "johndoe-99999/20221122/foo(bar/image-00000.dcm"),
            ],
            "99999_CT1_6168:foo_bar2": [
                str(source_dir / "johndoe-99999/20221122/foo,bar/image-00000.dcm"),
            ],
            "99999_CT1_6168:foo_bar3": [
                str(source_dir / "johndoe-99999/20221122/foo_bar/image-00000.dcm"),
            ],
        },
    }


@pytest.fixture(scope="session")
def xnat_connection():
    xnat4tests.start_xnat()
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
    FIELDS = ["Subject", "Session", "Dataset"]
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
    matcher = Matcher({"test": case["patterns"]}, MAPPINGS, FIELDS)
    return matcher, case
