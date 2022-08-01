from xnatuploader.matcher import Matcher
from pathlib import Path

CASES = [
    {
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
    }
]

MAPPINGS = {
    "Subject": ["Subject"],
    "Session": ["YYYY", "MM", "DD"],
    "Dataset": ["Filename"],
}


def filematch_to_dict(fm):
    return {"Subject": fm.subject, "Session": fm.session, "Dataset": fm.dataset}


def test_match():
    for case in CASES:
        config = {"paths": {"test": case["patterns"]}, "mappings": MAPPINGS}
        matcher = Matcher(config)
        for path in case["paths"]:
            results = matcher.match(Path(path["path"]))
            assert filematch_to_dict(results) == path["values"]
