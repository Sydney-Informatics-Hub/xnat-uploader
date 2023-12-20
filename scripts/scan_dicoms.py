#!/usr/bin/env python

from pydicom import dcmread
from pathlib import Path

DIR = "./"

# Added a comment to trigger pre-commit

for dicom in Path(DIR).glob("**/*.dcm"):
    dc = dcmread(dicom)
    try:
        image_type = dc.ImageType
    except Exception:
        image_type = ["-", "-", "-"]
    if type(image_type) is not list:
        image_type = [image_type]
    print(f"{dicom},{dc.Modality}," + ",".join(image_type))
