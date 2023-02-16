# xnatuploader

A command-line tool for uploading batches of DICOMS to an XNAT server, building
on the [xnatutils](https://github.com/Australian-Imaging-Service/xnatutils) library.

* [Usage](#usage)
  - [Initialising the spreadsheet](#initialising-the-spreadsheet)
  - [Scanning for files](#scanning-for-files)
  - [Uploading files](#uploading-files)
  - [Interrupting and restarting](#interrupting-and-restarting)
* [Finding files](#finding-files)
  - [Path matching](#path-matching)
  - [XNAT hierarchy mapping](#xnat-hierarchy-mapping)
  - [Matching example](#matching-example)
  - [Checking the spreadsheet](#checking-the-spreadsheet)
* [Installation](#installation)
* [Upgrading](#upgrading)

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

## Windows

From the Start menu, select the Anaconda prompt. Once the Anaconda prompt is
opened, you'll need to activate the conda environment in which xnatuploader
was installed:

    conda activate xnatuploader

## Initialisation

xnatuploader is run by typing commands at the Anaconda prompt or terminal:

### Initialising the spreadsheet

`xnatuploader init --spreadsheet spreadsheet.xlsx`

This initialises a spreadsheet with a single worksheet with default
configuration values. Details of the configuration are in the [section on finding files](#finding-files).

### Scanning for files

`xnatuploader scan --spreadsheet spreadsheet.xlsx --dir data_files`

This scans the directory `data_files` for DICOMs and builds a list of files
and metadata, which is stored in the spreadsheet as a new worksheet named
'Files'.

### Uploading files

`xnatuploader upload --spreadsheet spreadsheet.xlsx --dir data_files --project Test001 --server https://xnat.institution.edu/`

This command will prompt you for your username and password on the XNAT server,
read all the files from the spreadsheet and attempt to upload them.

The files will be uploaded to the project specified, using XNAT's hierarchy:

* Subject (research participant or patient)
* Session (experiment or visit)
* Dataset (a scan)

A Session can have multiple datasets, and a dataset will typically have many
individual DICOM files.

The subject, session and dataset are based on the metadata values are extracted
in the scanning pass. See the [Finding files](#finding-files) section below for more details and
configuration instructions.

The upload command needs to know both the URL of the XNAT server and a project
ID on the server to which the scans will be added. The project must already
exist, and you must have the right access level to add scans to it.

You can also configure the XNAT URL and project ID in the spreadsheet - see
the screenshot below for an example. If you specify an XNAT server or project
ID as options on the command line, these values will be used in preference to
the values in the spreadsheet.

### Interrupting and restarting

When a file can't be uploaded due to a network error, or the integrity check for
the upload fails, this error will be recorded in the spreadsheet and a warning
will be printed to the command line. If you re-run the upload, the program will
try to re-upload those files which didn't successfully upload on earlier runs.

While uploading is in progress, two progress bars will be shown on the command
line. One shows the progress at a high level, with a step for every dataset in
the upload (note that a single patient may have more than one dataset). The
second progress bar shows a step for every file in the current dataset.

You can interrupt the upload by pressing Ctrl-C. If you do this, the program
will prompt you to confirm whether you really want to stop. If you confirm,
the current progress will be written back to the spreadsheet, and all files
which haven't yet been uploaded will have a status written to indicate that
the upload was interrupted. If you re-run the upload with the same spreadsheet,
it will continue from where it was interrupted.

## Finding files

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

Configuration for inferring the XNAT values is in two sections, "Paths" and
"Mappings", which correspond to two steps:

1. "Paths" tells the script how to matching patterns against the filepath to create values
2. "Mappings" assigns those values, or DICOM metadata values, to the XNAT hierarchy


### Path matching

The "Paths" section of the config is one or more lists of patterns to be matched
against paths. Each set of patterns starts with a label - in the example above,
the label is "Nested". Each cell to the right of the label will be matched
against one or more directory names in each of the filepaths, from left to 
right

If all matches are successful, that path will be marked as a row
to be uploaded in the spreadsheet, and the values captured from the path will
be assigned to the XNAT hierarchy values according to the "Mappings" section
of the config worksheet.

The parts of the patterns in curly brackets like `{SubjectName}` are used to
capture values. Patterns which are in all caps, such as `{YYYY}` or `{II}`,
will only match numbers with the specified number of digits. All other 
patterns, for example `{SubjectName}`, will match any sequence of characters.

There are two special patterns, `*` and `**`. `*` matches a single directory
with any name, and `**` matches one or more directories with any name. `**`
lets you construct a pattern which will match files which might be nested at
different levels for different patients.

Note: if one set of patterns isn't flexible enough to match all the ways in
which scans are stored in the directory, you can add extra patterns as new
rows in the spreadsheet. Each set of patterns needs a unique label.
Sets of patterns will be matched in order from the top, and the first one
which succeeds will be used.

### XNAT hierarchy mapping

The "Mapping" section tells the script how to build the three XNAT hierarchy
values, Subject, Session and Dataset, based on values captured from the paths
and/or metadata fields read from the DICOM files. In the example, we're setting
the Subject to the `ID` value, the Session to the `StudyDate` values extracted
from the DICOMs, and the Dataset to the `Directory` value.

### Matching example

Here's a step-by-step illustration of how the set of patterns in the example
is matched against a filepath:

```
Doe^John-0001/20200312/Chest CT/scan0000.dcm
```

* `{SubjectName}-{ID}` matches `Doe^John-0001`, setting the values `SubjectName` to "Doe^John" and `ID` to "0001"
* `**` matches `20200312`, and does not set any values
* `{Directory}` matches `Chest CT` and sets the value `Directory` to "Chest CT"
* `{filename}.dcm` matches `scan0000.dcm` and sets the value `filename` to "0001"

The XNAT hierarchy values are then built according to the rules in the
"Mapping" section:

* `Subject` is set to the value stored in `ID`: **0001**
* `Session` is set to the value extracted from the DICOM metadata field `StudyDate`
* `Dataset` is set to the value stored in `Directory`: **Chest CT**

Note that not every value captured from the path needs to be used in "Mapping",
as `SubjectName` and `filename` are ignored.

The filename for the purposes of uploading will be automatically generated from
the path itself.

### Checking the spreadsheet

By default, all files which match a pattern are marked as selected for upload
in the spreadsheet. Before uploading, you can edit the spreadsheet to
deselect files or groups of files which shouldn't be uploaded.

By default, files for which no match succeeds won't be written to the
spreadsheet. You can run a scan with the `--unmatched` flag, which will 
write a row for every file whether or not the match succeeds:

`xnatuploader scan --spreadsheet spreadsheet.xlsx --dir data_files --unmatched`

This can be useful for figuring out why files aren't matching patterns.

## Installation

If you're on Windows, you'll need to install [Anaconda](https://docs.anaconda.com/anaconda/install/windows/), which will install the Python programming language and environment manager 
on your PC.

Open the Anaconda prompt via the Start menu.

If you're on a Mac or Linux, you can also install Conda using the relevant
installer, and just use a terminal for the rest of the installation instructions.

```
conda create -n xnatuploader
```
This will create a separate Python environment in which we'll install 
xnatuploader. Answer 'Y' when it prompts you to proceed.

```
conda activate xnatuploader
```

This activates the Python environment you've just created

```
pip install xnatuploader
```

This will download and install the latest version of xnatuploader. To check that
everything has worked after the upload and installation has finished, type the
following:

```
xnatuploader --help
```

You should get a message like the following:

```
usage: XNAT batch uploader [-h] [--dir DIR] [--spreadsheet SPREADSHEET]
                           [--server SERVER] [--project PROJECT]
                           [--loglevel LOGLEVEL] [--debug] [--logdir LOGDIR]
                           [--test] [--unmatched] [--overwrite]
                           {init,scan,upload,help}

positional arguments:
  {init,scan,upload,help}
                        Operation

optional arguments:
  -h, --help            show this help message and exit
  --dir DIR             Base directory to scan for files
  --spreadsheet SPREADSHEET
                        File list spreadsheet
  --server SERVER       XNAT server
  --project PROJECT     XNAT project ID
  --loglevel LOGLEVEL   Logging level
  --debug               Debug mode: only attempt to match 10 patterns and
                        generates a lot of debug messages
  --logdir LOGDIR       Directory to write logs to
  --test                Test mode: don't upload, just log what will be
                        uploaded
  --unmatched           Whether to include unmatched files in list
  --overwrite           Whether to overwrite files which have already been
                        uploaded
```

## Upgrading

To get the latest version of xnatuploader, type the following (at the Anaconda
prompt or terminal):

```
pip install --upgrade xnatuploader
```

