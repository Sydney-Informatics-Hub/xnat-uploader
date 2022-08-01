from xnatuploader.matcher import Matcher
from pathlib import Path
import random
import string
from datetime import datetime, timedelta


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
            }
        ],
    },
    "one_glob": {
        "patterns": ["{Subject}", "*", "{YYYY}{MM}{DD}", "{Filename}"],
        "paths": [
            {
                "path": "JoeBlow/ignoreMe/20120301/test.dcm",
                "values": {
                    "Subject": "JoeBlow",
                    "Session": "20120301",
                    "Dataset": "test.dcm",
                },
            }
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
            }
        ],
    },
}

MAPPINGS = {
    "Subject": ["Subject"],
    "Session": ["YYYY", "MM", "DD"],
    "Dataset": ["Filename"],
}


def random_word():
    n = random.randint(4, 20)
    return "".join([random.choice(string.ascii_letters) for i in range(n)])


def random_date():
    dt = datetime.now() - timedelta(days=random.randint(1, 10000))
    return dt.strftime("%Y%m%d")


def pattern_to_path(pattern, subject, session, filename):
    dirs = []
    for part in pattern:
        if part == "*":
            dirs.append(random_word())
        elif part == "**":
            dirs.extend([random_word() for i in range(random.randint(1, 10))])
        elif part == "{Subject}":
            dirs.append(subject)
        elif part == "{YYYY}{MM}{DD}":
            dirs.append(session)
        elif part == "{Filename}":
            dirs.append(filename)
    return "/".join(dirs)


def make_random_path(pattern):
    """
    Given a pattern, generates a random path which it will match, and
    the values which should be matched from it, expanding wildcards as
    necessary.
    """
    subject = random_word()
    session = random_date()
    filename = random_word() + ".dcm"
    path = pattern_to_path(pattern, subject, session, filename)
    return path, {"Subject": subject, "Session": session, "Dataset": filename}


def filematch_to_dict(fm):
    return {"Subject": fm.subject, "Session": fm.session, "Dataset": fm.dataset}


def test_match():
    for label, case in CASES.items():
        config = {"paths": {"test": case["patterns"]}, "mappings": MAPPINGS}
        matcher = Matcher(config)
        for path in case["paths"]:
            results = matcher.match(Path(path["path"]))
            assert filematch_to_dict(results) == path["values"]


def test_random():
    for label, case in CASES.items():
        config = {"paths": {"test": case["patterns"]}, "mappings": MAPPINGS}
        matcher = Matcher(config)
        for i in range(1000):
            path, expect = make_random_path(case["patterns"])
            results = matcher.match(Path(path))
            assert filematch_to_dict(results) == expect
