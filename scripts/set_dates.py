#!/usr/bin/env python

import argparse
from pydicom import dcmread
from pathlib import Path


def set_dates(file, date):
    dc = dcmread(file)
    dc["StudyDate"].value = date
    dc["AcquisitionDate"].value = date
    dc["ContentDate"].value = date
    dc.save_as(file)


if __name__ == "__main__":
    ap = argparse.ArgumentParser("Utility to set dates on DICOMs")
    ap.add_argument("--date", default="", type=str, help="Date YYYYMMDD")
    ap.add_argument("files", type=Path, nargs="+")
    args = ap.parse_args()
    if not args.date:
        print("you need to specify a date")
    else:
        for file in args.files:
            print(f"Setting {file} dates to {args.date}")
            try:
                set_dates(file, args.date)
            except KeyError as e:
                print(e)
