#!/bin/env python

import argparse

from pathlib import Path
from openpyxl import Workbook
from recipe import load_recipes, match_recipe


def scan_files(params, recipes, root, logfile):
    """
    Scan the filesystem under root for files which match recipes and write
    out the resulting values to a spreadsheet.
    ---
    params: set of all parameters for the recipes
    recipes: dict of { str: [ re.Pattern ] }
    root: pathlib.Path
    logfile: pathlib.Path
    """
    wb = Workbook()
    ws = wb.active
    ws.append(["Label", "File"] + params)
    for file in root.glob("**/*"):
        label, values = match_recipes(recipes, file)
        if label:
            row = [values[p] for p in params]
            ws.append([label, str(file)] + row)
    wb.save(logfile)


def match_recipes(recipes, file):
    """
    Try to match a filepath against each of the recipes and return the label
    and values for the first one which matches.
    ---
    recipes: dict of { str: [ re.Pattern ] }
    file: pathlib.Path

    returns: tuple of str, dict of { str: str }
                     or tuple of None, None
    """
    for label, recipe in recipes.items():
        values = match_recipe(recipe, file)
        if values:
            return label, values
    return None, None


def upload(args):
    pass


def show_help():
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
        params, recipes = load_recipes(args.recipe)
        scan_files(params, recipes, args.source, args.log)


if __name__ == "__main__":
    main()
