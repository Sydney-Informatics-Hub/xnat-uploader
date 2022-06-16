#!/usr/bin/env python


import argparse
import json
import logging
from pathlib import Path
import xnatutils
from openpyxl import Workbook, load_workbook

from xnatuploader.matcher import Matcher

FILE_COLUMN_WIDTH = 50


def new_workbook(matcher):
    """
    Make a new openpyxl workbook with headers from the matcher object
    and niceties such as a wider column for the file names
    ---
    matcher: a Matcher
    returns: a Workbook
    """
    wb = Workbook()
    ws = wb.active
    ws.column_dimensions["B"].width = FILE_COLUMN_WIDTH
    ws.title = "Files"
    ws.append(matcher.headers)
    return wb


def scan(matcher, root, logfile, include_unmatched=True):
    """
    Scan the filesystem under root for files which match recipes and write
    out the resulting values to a spreadsheet.
    ---
    matcher: a PathMatcher
    root: pathlib.Path
    logfile: pathlib.Path
    include_unmatched: bool
    """
    wb = new_workbook(matcher)
    ws = wb.active
    for file in root.glob("**/*"):
        filematch = matcher.match(file)
        logging.debug(f"File {filematch.file} match {filematch.values}")
        if filematch.values is not None or include_unmatched:
            if filematch.values is not None:
                logging.info(f"Matched {filematch.file}")
            ws.append(filematch.columns)
    wb.save(logfile)


def upload(xnat_session, matcher, project, logfile):
    """
    Load an Excel logfile created with scan and upload the files which the user
    has marked for upload, and which haven't been uploaded yet. Keeps track of
    successful uploads in the "success" column.
    ---
    xnat_session: an XnatPy session, as returned by xnatutils.base.connect
    matcher: a Matcher
    project: the XNAT project id to which we're uploading
    logfile: pathlib.Path to the Excel spreadsheet listing files
    """
    wb = load_workbook(logfile)
    ws = wb.active
    header = True
    files = []
    for row in ws.values:
        if header:
            header = False
        else:
            matchfile = matcher.from_spreadsheet(row)
            files.append(matchfile)

    # fixme: need to write out the spreadsheet progressively as we do the
    # uploads if this is going to work with interrupted connections etc
    for file in files:
        if file.selected:
            if file.status == "success":
                logging.info(f"{file.file} already uploaded")
            else:
                try:
                    logging.info(f"Uploading: {file.file}")
                    upload_file(xnat_session, project, file)
                    file.status = "success"
                except Exception as e:
                    logging.warning(f"Upload {file.file} failed: {e}")
                    file.error = str(e)
                    file.status = "failed"
        else:
            logging.debug(f"{file.file} not selected")
    wb = new_workbook(matcher)
    ws = wb.active
    for file in files:
        logging.warning(f"rewriting row for {file.file}: {file.columns}")
        logging.warning(f"xnat params = {file.xnat_params}")
        logging.warning(f"values = {file.values}")
        logging.warning(f"status = {file.status}")
        ws.append(file.columns)
    wb.save(logfile)


def upload_file(xnat_session, project, matchfile):
    xnatutils.put(
        matchfile.xnat_params["Session"],
        matchfile.xnat_params["Dataset"],
        matchfile.file,
        resource_name="DICOM",
        project_id=project,
        subject_id=matchfile.xnat_params["Subject"],
        create_session=True,
        connection=xnat_session,
    )


def show_help():
    pass


def main():
    ap = argparse.ArgumentParser("XNAT batch uploader")
    ap.add_argument(
        "--config", default="config.json", type=Path, help="JSON config file"
    )
    ap.add_argument(
        "--source", default="./", type=Path, help="Base directory to scan for files"
    )
    ap.add_argument(
        "--list", default="list.xlsx", type=Path, help="File list spreadsheet"
    )
    ap.add_argument("--server", type=str, help="URL of XNAT server")
    ap.add_argument("--project", type=str, help="XNAT project ID")
    ap.add_argument("--loglevel", type=str, default="info", help="Logging level")
    ap.add_argument(
        "--unmatched",
        action="store_true",
        default=False,
        help="Whether to include unmatched files in list",
    )
    ap.add_argument(
        "operation",
        default="scan",
        choices=["scan", "upload", "help"],
        help="Operation",
    )
    args = ap.parse_args()

    logging.basicConfig(level=args.loglevel.upper())

    if args.operation == "help":
        show_help()
        exit()

    with open(args.config, "r") as fh:
        config_json = json.load(fh)
        matcher = Matcher(config_json)

    if args.operation == "scan":
        logging.info(f"Scanning {args.source}")
        scan(matcher, args.source, args.list, include_unmatched=args.unmatched)
    else:
        if not args.server:
            logging.error("Can't upload without a server")
            exit()
        if not args.project:
            logging.error("Can't upload without a project ID")
            exit()
        xnat_session = xnatutils.base.connect(args.server)
        upload(xnat_session, matcher, args.project, args.list)


if __name__ == "__main__":
    main()
