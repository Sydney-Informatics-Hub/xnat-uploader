# xnatuploader

A command-line tool for uploading batches of DICOMS to an XNAT server, building
on the [xnatutils](https://github.com/Australian-Imaging-Service/xnatutils) library.

## Installation

If you're on Windows, you'll need to install [Anaconda](https://docs.anaconda.com/anaconda/install/windows/), which will install the Python programming language and environment manager 
on your PC.


## Usage

xnatuploader uses a 'two pass' approach to uploading files to an XNAT server.
The first pass scans a directory for files to upload, builds a list of
the files and their associated metadata and saves the list as a spreadsheet.
The second pass reads the spreadsheet and uploads the files to XNAT.

On the second pass, the status of each file upload - whether it was successful,
and any error messages if the upload failed - is written back to the spreadsheet.

The second pass can be re-run using the updated spreadsheet - files which have
been successfully uploaded already will be skipped, and files which were not
uploaded on earlier runs will be re-attempted.

The details of how xnatuploader gets metadata for each file are configured
using the spreadsheet: xnatuploader can write out a pre-initialised spreadsheet
before you run the first pass.

xnatuploader is run by typing commands at the Anaconda prompt or terminal:

### init

`xnatuploader init --spreadsheet spreadsheet.xlsx`

This initialises a spreadsheet with a single configuration worksheet

### scan

`xnatuploader scan --spreadsheet spreadsheet.xlsx --dir data_files`

This scans the directory `data_files` for DICOMs and builds a list of files
and metadata, which is stored in the spreadsheet as a new worksheet named
'Files'.

### upload

`xnatuploader upload --spreadsheet spreadsheet.xlsx --dir data_files`

This goes through the files in the spreadsheet and attempts to upload them
to XNAT. The files will be uploaded into XNAT's heirarchy:

* Subject (research participant or patient)
* Session (experiment or visit)
* Dataset (a scan)

A Session can have multiple datasets, and a dataset will typically have many
individual DICOM files.

The subject, session and dataset are based on the metadata values are extracted
in the scanning pass. See the Scanning section below for more details and
configuration instructions.

## Scanning

When `xnatupload scan` is run, it scans the specified directory for files to
upload. The scan looks for files at every level of the subdirectories within
the directory, and tries to match values in the filepaths which can be used
to determine how the files should be uploaded to XNAT.

Here's an example of a directory structure with scans for two patients.
The top-level directories have the naming convention SURNAME^GIVENNAME-ID.
Inside each patient's directory is a directory named for the date of their
visit in YYYYMMDD format, and inside those is one or more directories for
each type of scan they recieved on the visit. These directories contain
the actual DICOM files for the scan.

```
Doe^John-0001/20200312/Chest CT/scan0000.dcm
Doe^John-0001/20200312/Chest CT/scan0001.dcm
Doe^John-0001/20200312/Chest CT/scan0002.dcm
Roe^Jane-0342/20190115/Head CT/scan0000.dcm
Roe^Jane-0342/20190115/Head CT/scan0001.dcm
Roe^Jane-0342/20190115/Head CT/scan0002.dcm
Roe^Jane-0342/20190115/Head CT/scan0003.dcm
Roe^Jane-0342/20200623/Head CT/scan0000.dcm
Roe^Jane-0342/20200623/Head CT/scan0001.dcm
Roe^Jane-0342/20200623/Head CT/scan0002.dcm
Roe^Jane-0342/20200623/Neck CT/scan0000.dcm
Roe^Jane-0342/20200623/Neck CT/scan0001.dcm
Roe^Jane-0342/20200623/Neck CT/scan0002.dcm
Roe^Jane-0342/20200623/Neck CT/scan0003.dcm
```

To transform these filepaths into XNAT hierarchy values, we need to tell
xnatuploader to get the ID from the top-level directory and the scan type from 
the name of the directories containing the DICOM files ("Chest CT", "Head CT"
and so on).

We also need to get the session date. This could be done using the second
level of directories, but it's safer to get it from the DICOM
metadata, which will have a value StudyDate with the date of the scan.

Here is a configuration worksheet which will get the correct XNAT values
from this directory layout.

![A screenshot of a spreadsheet](doc/spreadsheet_config.png?raw=true "A screenshot of a spreadsheet")

The script turns a filelpath into XNAT hierachies in two steps:

1. Matching patterns against the filepath to create values
2. Assigning those values, or DICOM metadata values, to the XNAT hierarchy


## Pattern matching



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


The third pass reads in the spreadsheet and uses the extracted values to
upload each file to XNAT. The spreadsheet is used to keep track of which
files have been successfully uploaded, so that if the upload is interrupted
or doesn't succeed for some files, it can be re-run without trying to upload
those files which have already succeeded.



    xnatuploader --spreadsheet list.xlsx --server http://xnat.server/ --project MyProject upload

This reads back the values written out to the list.xlsx spreadsheet and
uses them to upload the selected files to the selected project on XNAT.
Authentication works the same way as xnatutils - the user is prompted for their
username and password, and the encrypted values are cached in a .netrc file 

The spreadsheet will be updated to indicate the status of each uploaded file.

If the upload is interrupted, it can be restarted by running the same command:
files marked as having been uploaded successfully will be skipped.

