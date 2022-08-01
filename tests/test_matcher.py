from pathlib import Path
import random
import string
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def test_match(matcher_case):
    matcher, case = matcher_case
    for path in case["paths"]:
        results = matcher.match(Path(path["path"]))
        assert filematch_to_dict(results) == path["values"]


def test_no_match(matcher_case):
    matcher, case = matcher_case
    if "bad_paths" in case:
        for bad_path in case["bad_paths"]:
            results = matcher.match(Path(bad_path))
            assert not results.success
            assert results.error == "Unmatched"


def test_random(matcher_case):
    matcher, case = matcher_case
    for i in range(5):
        path, expect = make_random_path(case["patterns"])
        results = matcher.match(Path(path))
        assert filematch_to_dict(results) == expect


def random_word():
    n = random.randint(4, 20)
    return "".join([random.choice(string.ascii_letters) for i in range(n)])


def random_date():
    dt = datetime.now() - timedelta(days=random.randint(1, 10000))
    return dt.strftime("%Y%m%d")


def pattern_to_path(pattern, subject, session, filename):
    """
    Given a matcher pattern and a subject, session and filename, return
    a path which that pattern should match. This assumes that the pattern
    contains {Subject}, {YYYY}{MM}{DD} and {Filename} and that these mappings
    will be used in the Matcher.
    """
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
