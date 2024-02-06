from pathlib import Path
import random
import string
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Note: this test is a little clunky because Matcher.match now does DICOM
# lookups, so it requires a file to work on. These tests are just about
# path value extraction, which is why we're testing match_path.


def test_match(matcher_case):
    matcher, case = matcher_case
    for path in case["paths"]:
        _, results = matcher.match_path(Path(path["path"]))
        assert results == path["values"]


def test_no_match(matcher_case):
    matcher, case = matcher_case
    if "bad_paths" in case:
        for bad_path in case["bad_paths"]:
            _, results = matcher.match_path(Path(bad_path))
            assert is_incomplete(results)  #


def test_random(matcher_case):
    matcher, case = matcher_case
    for i in range(100):
        path, expect = make_random_path(case["patterns"])
        _, results = matcher.match_path(Path(path))
        assert results == expect


def random_word():
    n = random.randint(4, 20)
    return "".join([random.choice(string.ascii_letters) for i in range(n)])


def random_id():
    n = random.randint(1, 8)
    return "".join([random.choice(string.digits + "._") for i in range(n)])


def random_date():
    dt = datetime.now() - timedelta(days=random.randint(1, 10000))
    return dt.strftime("%Y%m%d")


def pattern_to_path(pattern, subject, subjectid, session, filename):
    """
    Given a matcher pattern and a subject, session and filename, return
    a path which that pattern should match. This assumes that the pattern
    contains {name}-{ID}, {DDDDDDDD} and {Filename} and that these mappings
    will be used in the Matcher.
    """
    dirs = []
    for part in pattern:
        if part == "*":
            dirs.append(random_word())
        elif part == "**":
            dirs.extend([random_word() for i in range(random.randint(1, 10))])
        elif part == "{SubjectName}-{ID}":
            dirs.append(subject + "-" + subjectid)
        elif part == "{DDDDDDDD}":
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
    subjectid = random_id()
    session = random_date()
    filename = random_word() + ".dcm"
    path = pattern_to_path(pattern, subject, subjectid, session, filename)
    return path, {
        "SubjectName": subject,
        "ID": subjectid,
        "DDDDDDDD": session,
        "Filename": filename,
    }


def is_incomplete(values):
    """
    A hack because match_path doesn't always return None on a bad match
    """
    if values is None:
        return True
    if "name" not in values:
        return True
    if "ID" not in values:
        return True
    if "DDDDDDDD" not in values:
        return True
    if "Filename" not in values:
        return True
