# README

User requirements / story:

I have a collection of directories, which have subdirectories, which contain
scans. I want to:

- upload some (or all) of these to XNAT
- not have to do this manually
- be able to restart the process and not redo too much if the network drops out

Design:

A recipe / config for mapping directory and filenames to parameters for the
session.

For example: this is Dan Jackson's format

SURNAME^GIVENNAME-UNIQUENUMBER   (eg. CITIZEN^JOHN-1001) 
yyyymmdd-ScanName   (eg. 20140903-CT Chest,Abdo,Pelvis)
yyyymmdd-ScanName   (eg. 20150601-HRCT Chest)
yyyymmdd-ScanName   (eg. 20150601-CT Chest)

SURNAME^GIVENNAME-UNIQUENUMBER   (eg. CITIZEN^MARY-1002) 
yyyymmdd-ScanName   (eg. 20001030-CT Chest)
yyyymmdd-ScanName   (eg. 20001201-HRCT Chest)
yyyymmdd-ScanName   (eg. 20010106-CT Chest, Pelvis)

A recipe for this might look like

Folder: {surname}^{givenname}-{identifier}
File: {yyyy}{mm}{dd}-{name}

The script would then traverse the filesystem and try to match these against
directories and files, and either do the uploading, or build a spreadsheet
of what it's going to upload, for verification before actually uploading