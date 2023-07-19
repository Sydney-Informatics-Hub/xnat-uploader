#!/usr/bin/env python


from dicomanonymizer import anonymize, keep
from pydicom import dcmread

from pydicom.tag import Tag


INFILE = "./anonymizer/000000.dcm"
OUTFILE = "./anonymizer/000000_anon.dcm"

CUSTOM_RULES = {(0x0010, 0x0020): keep, (0x0010, 0x0010): keep}

CUSTOM_RULES_KEYWORDS = {"StudyDate": keep, "AccessionNumber": keep}

rules = {}

for keyword, action in CUSTOM_RULES_KEYWORDS.items():
    try:
        tag = Tag(keyword)
        rules[(tag.group, tag.elem)] = action
    except ValueError as e:
        print(f"{e} Unknown DICOM keyword {keyword}")

print(rules)


anonymize(INFILE, OUTFILE, rules, True)

dc = dcmread(OUTFILE)

print("Anonymised metadata:")
print(dc)
