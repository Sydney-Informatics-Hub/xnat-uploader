# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3]

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