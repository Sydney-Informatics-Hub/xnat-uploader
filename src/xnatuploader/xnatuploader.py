#!/usr/bin/env python

import argparse
import logging
import sys
from pathlib import Path
import xnatutils
from openpyxl import load_workbook

from xnatuploader.matcher import Matcher
from xnatuploader.workbook import new_workbook, add_filesheet, load_config
from xnatuploader.upload import Upload

FILE_COLUMN_WIDTH = 50

logger = logging.getLogger(__name__)


def scan(matcher, root, spreadsheet, include_unmatched=True):
    """
    Scan the filesystem under root for files which match recipes and write
    out the resulting values to a new worksheet in the spreadsheet.
    ---
    matcher: a PathMatcher
    root: pathlib.Path
    spreadsheet: pathlib.Path
    include_unmatched: bool
    """
    wb = load_workbook(spreadsheet)
    ws = add_filesheet(wb, matcher)
    count = 0
    matches = 0
    for file in root.glob("**/*"):
        if file.is_file():
            count += 1
            logger.debug(f"Scanning {file}")
            filematch = matcher.match(file)
            if filematch.values is not None:
                matches += 1
                logger.debug(f"Matched {filematch.file}")
                ws.append(filematch.columns)
            else:
                if include_unmatched:
                    ws.append(filematch.columns)
    logger.info(f"Scanned {count} files under {root}")
    logger.info(f"Saved {matches} matching files to {spreadsheet}")
    wb.save(spreadsheet)


def upload(xnat_session, matcher, project, spreadsheet, test=False, overwrite=False):
    """
    Load an Excel spreadsheet created with scan and upload the files which the user
    has marked for upload, and which haven't been uploaded yet. Keeps track of
    successful uploads in the "status" column.
    ---
    xnat_session: an XnatPy session, as returned by xnatutils.base.connect
    matcher: a Matcher
    project: the XNAT project id to which we're uploading
    spreadsheet: pathlib.Path to the Excel spreadsheet listing files
    overwrite: Boolean, used to set the overwrite flag on xnatutils for testing
    """
    wb = load_workbook(spreadsheet)
    ws = wb["Files"]
    header = True
    files = []
    for row in ws.values:
        if header:
            header = False
        else:
            matchfile = matcher.from_spreadsheet(row)
            files.append(matchfile)
    uploads = collate_uploads(project, files)
    ws = add_filesheet(wb, matcher)
    try:
        wb.save(spreadsheet)
    except PermissionError:
        logger.error(
            f"""
Upload cancelled because a permissions error prevented the script from writing
to {spreadsheet}.

If you are on Windows, this may be because you have the spreadsheet open in
Excel. Try closing the spreadsheet and running the script again.
"""
        )
        sys.exit()
    for session_label, upload in uploads.items():
        error = None
        logger.info(f"Uploading to {session_label}")
        if test:
            upload.log(logger)
        else:
            try:
                upload.upload(xnat_session, project, overwrite)
            except Exception as e:
                logger.warning(f"Upload to  {session_label} failed: {e}")
                error = str(e)
            for file in upload.files:
                if error:
                    file.status = error
                else:
                    file.status = "success"
                ws.append(file.columns)
            wb.save(spreadsheet)


def collate_uploads(project_id, files):
    """
    Takes a list of files and collates them by subject (patient) and visit
    index (starting from the earliest). Returns a dict of Upload objects
    keyed by session labels.
    ---
    project_id: str
    files: list of FileMatch

    returns: dict of str: Upload
    """

    subjects = {}
    for file in files:
        if file.selected:
            if file.status == "success":
                logger.info(f"{file.file} already uploaded")
            else:
                if file.subject not in subjects:
                    subjects[file.subject] = []
                subjects[file.subject].append(file)

    uploads = {}
    for subject_id, files in subjects.items():
        dates = sorted(set([file.study_date for file in files]))
        visits = {dates[i]: i + 1 for i in range(len(dates))}
        for file in files:
            visit = visits[file.study_date]
            modality = file.modality
            session_label = f"{project_id}_{subject_id}_{modality}{visit}"
            file.session_label = session_label
            if session_label not in uploads:
                uploads[session_label] = Upload(
                    session_label,
                    subject_id,
                    modality,
                    file.dataset,
                )
            uploads[session_label].add_file(file)
    return uploads


def show_help():
    print(
        """
xnatuploader is a utility for collating and uploading images to XNAT, using
a spreadsheet to keep track of which files are uploaded.

Sample usage:

    xnatuploader --spreadsheet sheet.xlsx init

Writes out a spreadsheet in the format required by xnatuploader, with a sample
configuration page.

    xnatuploader --spreadsheet sheet.xlsx --dir ./source/ scan

Scans the directory provided with the --dir flag and builds a file list in
the spreadsheet

    xnatuploader --spreadsheet sheet.xlsx --dir ./source upload

Uploads the files recorded in the spreadsheet, to the server and project
specified in the config worksheet.

For more detailed instructions on how to configure xnatuploader to capture
parameters from filepaths, refer to the "Configuration" worksheet in the
spreadsheet, or visit the online documentation at:

https://github.com/Sydney-Informatics-Hub/xnat-uploader/

"""
    )


def opt_or_config(args, config, param):
    """
    Gets a config value from either a command line parameter or the config
    spreadsheet (in that order). Raises a ValueException if no value is
    available.
    ---
    args: Namespace as returned by argparse
    config: the config dict
    value: the key in the config dict
    """
    value = None
    params = vars(args)
    if param.lower() in params:
        value = params[param.lower()]
    if value is None:
        if param in config:
            value = config[param]
    if value is None:
        raise ValueError(f"{param} must be specified in config or via command line")
    return value


def main():
    ap = argparse.ArgumentParser("XNAT batch uploader")
    ap.add_argument(
        "--dir", default="./", type=Path, help="Base directory to scan for files"
    )
    ap.add_argument(
        "--spreadsheet", default="files.xlsx", type=Path, help="File list spreadsheet"
    )
    ap.add_argument("--server", type=str, help="XNAT server")
    ap.add_argument("--project", type=str, help="XNAT project ID")
    ap.add_argument("--loglevel", type=str, default="info", help="Logging level")
    ap.add_argument(
        "--logdir", type=Path, default="logs", help="Directory to write logs to"
    )
    ap.add_argument(
        "--test",
        action="store_true",
        default=False,
        help="Test mode: don't upload, just log what will be uploaded",
    )
    ap.add_argument(
        "--unmatched",
        action="store_true",
        default=False,
        help="Whether to include unmatched files in list",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Whether to overwrite files which have already been uploaded",
    )
    ap.add_argument(
        "operation",
        default="scan",
        choices=["init", "scan", "upload", "help"],
        help="Operation",
    )
    args = ap.parse_args()

    if not args.logdir.is_dir():
        args.logdir.mkdir(parents=True)

    logger.setLevel(logging.DEBUG)
    logfh = logging.FileHandler(args.logdir / "xnatuploader.log")
    logfh.setLevel(args.loglevel.upper())
    logger.addHandler(logfh)
    logch = logging.StreamHandler()
    logch.setLevel(args.loglevel.upper())
    logger.addHandler(logch)

    if args.operation == "help":
        show_help()
        exit()

    if args.operation == "init":
        new_workbook(args.spreadsheet)
        logger.info(f"Initialised spreadsheet at {args.spreadsheet}")
        exit()

    config = load_config(args.spreadsheet)

    matcher = Matcher(config)

    if args.operation == "scan":
        logger.info(f"Scanning directory {args.dir}")
        scan(matcher, args.dir, args.spreadsheet, include_unmatched=args.unmatched)
    else:
        server = opt_or_config(args, config["xnat"], "Server")
        project = opt_or_config(args, config["xnat"], "Project")
        logger.warning(f"Server = {server}")
        logger.warning(f"Project = {project}")
        xnat_session = xnatutils.base.connect(server)
        upload(
            xnat_session,
            matcher,
            project,
            args.spreadsheet,
            args.test,
            args.overwrite,
        )


if __name__ == "__main__":
    main()
