#!/usr/bin/env python

from pydicom import dcmread
from pathlib import Path

DIR = "tests/fixtures/source/ROE^JANE-397829"

for dicom in Path(DIR).glob("*.dcm"):
    print(f"Reading {dicom.name}")
    dc = dcmread(dicom)
    print(dc.Modality)
    print(dc.StudyDescription)
    print(dc.StudyDate)
