# xnatuploader

A command-line tool which builds on [xnatutils](https://github.com/Australian-Imaging-Service/xnatutils) to assist with uploading batches of DICOMs to XNAT.

## Usage

xnatuploader runs in three passes. The first pass writes out a spreadsheet with
a sample configuration page, which should be edited to match the file paths
you're going to scan.

The second pass scans a filesystem and looks for filepaths which match the
configured patterns, uses the pattern matches to deduce the subject, session
and dataset values for XNAT, and writes out a spreadsheet listing all of the
files, the pattern matches and the extracted XNAT values.

The third pass reads in the spreadsheet and uses the extracted values to
upload each file to XNAT. The spreadsheet is used to keep track of which
files have been successfully uploaded, so that if the upload is interrupted
or doesn't succeed for some files, it can be re-run without trying to upload
those files which have already succeeded.

## Initialisation

    xnatuploader --spreadsheet list.xlsx init


## Scanning

    xnatuploader --spreadsheet list.xlsx --dir images/ scan

### Pattern matching

A recipe is a list of patterns which are used to match against directories
and filenames and capture values from them. Matching works in two steps:
a path is matched against a recipe to capture values, and then those values
are mapped to the XNAT hierarchy Subject/Session/Dataset.

Here's an example of a recipe which looks for directories with the patient
name and ID separated by a "-", containing DICOM files with a name consisting
of the date in YYYYMMDD format, a "-" and a label or filename:

	[ "{SubjectName}-{SubjectId}", "{YYYY}{MM}{DD}-{Label}.dcm" ]

For a file with the following path:

    C:\User\xxyy\Scans\SMITH^JOHN-928302\20140903-CTChest.dcm

the above pattern would produce the following values:

    SubjectName = SMITH^JOHN
    SubjectId   = 928302
    YYYY        = 2014
    MM          = 09
    DD          = 03
    Label       = CTChest

Patterns are matched against the filepath in reverse, starting with
the filename, which is compared to the last pattern. If that matches, the
directory is compared to the second-last pattern, and so on. This means that
a single pattern can match files which are nested at different levels.

These values would then be mapped to XNAT values with the following mapping:

    [
    	"Subject": "SubjectId",
    	"Session": [ "YYYY", "MM", "DD" ],
    	"Dataset": "Label"
    ]

to give the XNAT values:

    Subject = 938302
    Session = 20140903
    Dataset = CTChest

A recipe can be given multiple patterns, in case a single pattern isn't
flexible enough to match all of the desired paths to be scanned.

### Checking the spreadsheet

By default, all files which match a pattern are marked as selected for upload
in the spreadsheet. Before uploading, you can edit the spreadsheet to
deselect files or groups of files which shouldn't be uploaded.

If the scan is run with the "unmatched" flag, all files will be included in 
the spreadsheet. Unmatched files will not be marked as selected for upload,
and would not be uploaded if selected, as they won't have values to be used as
XNAT categories. It's possible to add the XNAT hierarchy values manually to the
spreadsheet: files with manual values can be selected and will be uploaded.

## Uploading

    xnatuploader --spreadsheet list.xlsx --server http://xnat.server/ --project MyProject upload

This reads back the values written out to the list.xlsx spreadsheet and
uses them to upload the selected files to the selected project on XNAT.
Authentication works the same way as xnatutils - the user is prompted for their
username and password, and the encrypted values are cached in a .netrc file 

The spreadsheet will be updated to indicate the status of each uploaded file.

If the upload is interrupted, it can be restarted by running the same command:
files marked as having been uploaded successfully will be skipped.

