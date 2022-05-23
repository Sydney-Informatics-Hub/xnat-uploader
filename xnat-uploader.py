#!/bin/env python

import argparse
import os
from pathlib import Path
from openpyxl import Workbook

def show_help():
	pass








def scan(args):
	"""Walks a filesystem looking for DICOMs and trying to match them against
	the recipe, and builds a spreadsheet of the results"""

	# open spreadsheet
	for dicom in scan_files(args.source, args.recipe):
		# add row to spreadsheet
	#close spreadsheet



def scan_files(source, recipe):
	"""Scans the filesystem looking for matches and yielding results"""
	for root, files, dirs in os.walk(args.source):
		match = match_recipe(recipe, root, files):
		if match:
			yield match




def upload(args):
	pass


def main():
    ap = argparse.ArgumentParser("XNAT batch uploader")
    ap.add_argument("--recipe", default="recipe.json", type=Path)
    ap.add_argument("--source", default="./", type=Path)
    ap.add_argument("--log", default="upload_log.xls", type=Path)
    ap.add_argument("operation", default="scan", choices=["scan", "upload", "help"])
    args = ap.parse_args()

    if args.operation == "help":
    	show_help()
    elif args.operation == "upload":
    	upload(args)
    else:
    	scan(args)

if __name__ == "__main__":
    main()
