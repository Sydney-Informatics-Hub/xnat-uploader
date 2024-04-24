# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.9]

Bugfix:

- Fixed a bug which 1.1.8 introduced - not all DICOMs have ImageTypes

## [1.1.8]

Bugfix:

- Fixed an error in the DOSE_INFO check, which was assuming that ImageType
  always has three values

## [1.1.7]

Bugfix:

- Files with a value of DOSE_INFO in the third item of ImageType are now 
  always skipped when scanning, rather than this behaviour being dependent on
  config (introduced in 1.1.5) - this is because they have been breaking
  pipeline extraction on the server and leaving sessions with a blank
  StudyDate, so there's no real reason not to exclude them.

  An additional test was added to make sure DICOMs are ok before uploading them,
  and error handling around pipeline triggers has been improved.

## [1.1.6]

Bugfix:

- Filename matching had magical behaviour which treated the first character
  after a {capture} pattern as a delimiter, and excluded it from the capture -
  this meant that the pattern "{filename}.dcm" wouldn't match a file with 
  a period in the basename like "0000.0001.dcm".  Have removed the magical
  behaviour.

## [1.1.5]

Features:

- scanning can now be configured to skip files based on the values in the
  DICOM field ImageType. This allows us to skip DICOMS with an image type
  DOSE_INFO, which are documents (likely containing PID) rather than scan
  images, and which are also triggering a bug on the server which leaves the
  Study Date blank for the whole session.

## [1.1.4]

Features:

- the anonymization feature is now optional via the --anonymize flag
- collation of scans by session number is now optional via the --strict flag

## [1.1.3]

Features:

- Now uses the dicom-anonymizer library to make a local copy of each scan with
  identifying metadata fields stripped out or replaced with appropriate values.
  The default anonymisation behaviour can be configured with an AllowFields
  parameter.

## [1.1.2]

Bug fixes:

- Scan id is now set to the DICOM ServiceNumber - if it's different, XNAT
  creates a shadow record which won't be correctly deidentified

Enhancements:

- Refactored the code which extracts metadata from file paths and DICOMS - this
  makes xnatuploader easier to maintain, and also separates the XNAT-specific
  stuff from the file scanner, which means that it can later be spun off as
  its own library for building lists of files which aren't DICOMs

## [1.1.1]

Bug fixes:

- Added checks for reports / documents which are likely to contain identifying
  patient information (DICOM encapsulated documents and SR Structured Reports)


## [1.1.0]

Features:

- Added API calls to trigger metadata extraction and server pipelines
- added --version option

## [1.0.2]

Features:

- metadata for scanner manufacturer and model

Bug fixes:

- dates are being set correctly

## [1.0.1]

Bug fixes:

- Stopped the spreadsheet accumulating mutiple versions of the Files sheet
- Removed magic behaviour for {ID} parameter

## [1.0.0]

## [0.0.3]

Features:

- Progress bars
- Wildcards are more flexible
- DICOM metadata extraction can be configured in the spreadsheet
- now tested with uploads of 1000+ scan files

Bug fixes:

- All files for a session were being stored in a single scan type
- Spreadsheets were being corrupted when updated

## [0.0.2]

Features:

- Allow wildcards in path patterns
- improved user feedback when scanning directories
- feedback on permissions error from spreadsheet being open in Excel on Windows

Bug fixes:

- XNAT session and scan classes set correctly

### Added 

- Initial release

[0.0.1]: https://github.com/Sydney-Informatics-Hub/xnat-uploader/
