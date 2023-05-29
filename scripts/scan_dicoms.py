#!/usr/bin/env python

from pydicom import dcmread
from pathlib import Path

DIR = "tests/fixtures/"

for dicom in Path(DIR).glob("**/*.dcm"):
    dc = dcmread(dicom)
    print(
        f"{dicom},{dc.Modality},{dc.StudyDate},{dc.StudyDescription},{dc.SeriesNumber}"
    )
