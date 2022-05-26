# XNAT Uploader

Command-line tool for uploading moderately large collections of DICOM medical
image files to XNAT.

## Use case

I have a collection of directories, which have subdirectories, which contain
scans. I want to:

- upload some (or all) of these to XNAT
- not have to do this one at a time
- be able to restart the process and not redo too much if the network drops out


A recipe / config for mapping directory and filenames to parameters for the
session.

For example: this format:

SURNAME^GIVENNAME-UNIQUENUMBER   (eg. CITIZEN^JOHN-1001) 
yyyymmdd-ScanName   (eg. 20140903-CT Chest,Abdo,Pelvis)
yyyymmdd-ScanName   (eg. 20150601-HRCT Chest)
yyyymmdd-ScanName   (eg. 20150601-CT Chest)

SURNAME^GIVENNAME-UNIQUENUMBER   (eg. CITIZEN^MARY-1002) 
yyyymmdd-ScanName   (eg. 20001030-CT Chest)
yyyymmdd-ScanName   (eg. 20001201-HRCT Chest)
yyyymmdd-ScanName   (eg. 20010106-CT Chest, Pelvis)

A recipe for this might look like

[ "{surname}^{givenname}-{identifier}", "{yyyy}{mm}{dd}-{name}", "{file}" ]

The script will work in two passes.

### Scanning

Traverses the filesystem and builds a list of files which matched the recipe.
The list of files and extracted values is saved as an Excel file. Optionally,
files which didn't match any of the patterns are also recorded in the
spreadsheet

The spreadsheet has a column which allows the user to select / deselect files
to be uploaded.

### Uploading

Once the user has decided which files to upload, the script is run in upload
mode, and uses the metadata stored in the spreadsheet to add the files to XNAT.
It keeps track of which files have been successfully uploaded in the
spreadsheet, so that if it's interrupted and restarted it can skip those which
have already been uploaded.
