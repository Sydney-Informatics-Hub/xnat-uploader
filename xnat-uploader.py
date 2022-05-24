#!/bin/env python

import argparse
import os
import json
import re

from pathlib import Path
from openpyxl import Workbook
from recipe import load_recipes, match_recipe

def show_help():
	pass




def scan(source, recipes):
	"""Walks a filesystem looking for DICOMs and trying to match them against
	the recipe, and builds a spreadsheet of the results"""

	wb = Workbook()
	ws = wb.active
	for label, file, values in scan_files(source, recipes):
		print(label, file, values)
	return wb



def scan_files(source, recipes):
	"""Scans the filesystem looking for matches and yielding results"""

	for file in source.glob("**/*"):
		label, values = match_recipes(recipes, file)
		if label:
			yield label, file, values


def match_recipes(recipes, file):
	for label, recipe in recipes.items():
		values = match_recipe(recipe, file.parts)
		if values:
			return label, values
	return None, None 



def upload(args):
	pass


def main():
    ap = argparse.ArgumentParser("XNAT batch uploader")
    ap.add_argument("--recipe", default="recipe.json", type=Path)
    ap.add_argument("--source", default="./", type=Path)
    ap.add_argument("--log", default="log.xlsx", type=Path)
    ap.add_argument("operation", default="scan", choices=["scan", "upload", "help"])
    args = ap.parse_args()

    if args.operation == "help":
    	show_help()
    elif args.operation == "upload":
    	upload(args)
    else:
    	recipes = load_recipes(args.recipe)
    	wb = scan(args.source, recipes)
    	# wb.save(args.log)

if __name__ == "__main__":
    main()
