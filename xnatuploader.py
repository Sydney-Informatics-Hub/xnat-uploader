#!/usr/bin/env python


import argparse
import json

from pathlib import Path
from openpyxl import Workbook, load_workbook
from recipe import parse_recipes, match_recipe
import xnatutils

XNAT_HIERARCHY = ["subject", "session", "dataset"]


def load_config(config_file):
    """
    Load a JSON config file and return a list of params, a dict of recipes
    and a dict of mappings from XNAT values to lists of params
    TODO: refactor into a class?
    ---
    config_file: pathlib.Path

    Returns: tuple of ( list of str,
                        dict of { str: [ re.Pattern]},
                        dict of { str: [ str ] }
                        )
    """
    with open(config_file, "r") as fh:
        config = json.load(fh)
        params, recipes = parse_recipes(config["recipes"])
        mappings = config["mappings"]
    for k, vs in mappings.items():
        for v in vs:
            if v not in params:
                raise Exception(f"Value {v} in mapping for {k} not defined in a recipe")
    if set(mappings.keys()) != set(XNAT_HIERARCHY):
        raise Exception(f"Must have mappings for each of {XNAT_HIERARCHY}")
    return params, recipes, mappings


def map_values(values, mappings):
    """
    Given a dict of values which has been captured from a filepath by a recipe,
    try to map it to the XNAT hierarchy using the mappings

    values: dict of { str: str }
    mappings: dict of { str: [ str ] }
    """
    xnat_params = {}
    for xnat_cat, path_vars in mappings.items():
        xnat_params[xnat_cat] = "".join([values[v] for v in path_vars])
    return [xnat_params[xh] for xh in XNAT_HIERARCHY]


def scan_files(params, recipes, mappings, root, logfile):
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
    ws.append(["Recipe", "File", "Upload", "Status"] + XNAT_HIERARCHY + params)
    for file in root.glob("**/*"):
        label, values = match_recipes(recipes, file)
        if label:
            captures = [values[p] for p in params]
            try:
                xnat_params = map_values(values, mappings)
                ws.append([label, str(file), "Y", ""] + xnat_params + captures)
            except Exception as e:
                ws.append(
                    [label, str(file), "N", f"mapping error {e}", "", "", ""] + captures
                )
        else:
            ws.append(["", str(file), "N", "unmatched"])
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


def upload_file(xnat_session, project, subject, session, dataset, file):
    print(f"Upload: {project} {subject} {session} {dataset} {file}")
    xnatutils.put(
        session,
        dataset,
        file,
        resource_name="DICOM",
        project_id=project,
        subject_id=subject,
        create_session=True,
        connection=xnat_session,
    )


def upload(xnat_session, project, logfile):
    """
    Load an Excel logfile created with scan and upload the files which the user
    has marked for upload, and which haven't been uploaded yet. Keeps track of
    successful uploads in the "success" column
    """
    wb = load_workbook(logfile)
    ws = wb.active
    header = True
    files = []
    for row in ws.values:
        if header:
            columns = row
            header = False
        else:
            if row[2] == "Y":
                files.append(list(row))
    for file in files:
        if file[3] == "success":
            print(f"{file[1]} - already uploaded")
        else:
            try:
                # FIXMEEEEEE
                upload_file(xnat_session, project, file[4], file[5], file[6], file[1])
                file[3] = "success"
            except Exception as e:
                file[3] = f"failed: {e}"
    wb = Workbook()
    ws = wb.active
    ws.append(columns)
    for file in files:
        ws.append(file)
    wb.save(logfile)


def show_help():
    pass


def main():
    ap = argparse.ArgumentParser("XNAT batch uploader")
    ap.add_argument("--config", default="config.json", type=Path)
    ap.add_argument("--source", default="./", type=Path)
    ap.add_argument("--log", default="log.xlsx", type=Path)
    ap.add_argument("--server", type=str)
    ap.add_argument("--project", type=str)
    ap.add_argument("operation", default="scan", choices=["scan", "upload", "help"])
    args = ap.parse_args()

    if args.operation == "help":
        show_help()
        exit()

    params, recipes, mappings = load_config(args.config)

    if args.operation == "scan":
        scan_files(params, recipes, mappings, args.source, args.log)
    else:
        if not args.server:
            print("Can't upload without a server")
            exit()
        if not args.project:
            print("Can't upload without a project ID")
            exit()
        xnat_session = xnatutils.base.connect(args.server)
        upload(xnat_session, args.project, args.log)


if __name__ == "__main__":
    main()
