#!/usr/bin/env python


from dicomanonymizer import anonymize, keep
from pydicom import dcmread

INFILE = "./anonymizer/000000.dcm"
OUTFILE = "./anonymizer/000000_anon.dcm"

CUSTOM_RULES = {(0x0010, 0x0020): keep, (0x0010, 0x0010): keep}


anonymize(INFILE, OUTFILE, CUSTOM_RULES, True)

dc = dcmread(OUTFILE)

print("Anonymised metadata:")
print(dc)
