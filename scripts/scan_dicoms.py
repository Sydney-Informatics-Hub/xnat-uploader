#!/usr/bin/env python

from pydicom import dcmread
from pathlib import Path

DIR = "./"

for dicom in Path(DIR).glob("**/*.dcm"):
    dc = dcmread(dicom)
    try:
        image_type = dc.ImageType
    except Exception:
        image_type = ["-", "-", "-"]
    if not type(image_type) == list:
        image_type = [image_type]
    print(f"{dicom},{dc.Modality}," + ",".join(image_type))
