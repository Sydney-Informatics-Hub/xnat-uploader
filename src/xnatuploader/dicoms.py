import logging
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from xnatuploader.matcher import ExtractException, FileMatch

DICOM_PARAMS = [
    "Modality",
    "StudyDescription",
    "StudyDate",
    "Manufacturer",
    "ManufacturerModelName",
    "StationName",
]

SPREADSHEET_FIELDS = [
    "SessionLabel",
    "DICOM:Manufacturer",
    "DICOM:ManufacturerModelName",
    "DICOM:Modality",
    "DICOM:StationName",
    "DICOM:StudyDate",
    "DICOM:StudyDescription",
]

logger = logging.getLogger(__name__)


def dicom_extractor(file):
    """
    Try to extract DICOM metadata from a file, and check that it doesn't
    have an encapsulated document, or is of modality SR (which is a special
    type reserved for reports).

    Raises ExtractException if the file is not a DICOM, has an embedded
    report or the wrong modality
    ---
    file: pathlib.Path

    returns: {str: str}

    raises: DicomExtractException
    """
    logger.debug(f"> reading DICOM metadata {file}")
    values = None
    try:
        dc_meta = dcmread(file)
        values = {f"DICOM:{p}": dc_meta.get(p) for p in DICOM_PARAMS}
        logger.warning(f"> values {values}")
    except InvalidDicomError:
        raise ExtractException("File is not a DICOM")
    if "DICOM:EncapsulatedDocument" in values:
        raise ExtractException("DICOM has an encapsulated document")
    if "DICOM:Modality" not in values:
        raise ExtractException("DICOM has no modality")
    if values["DICOM:Modality"] == "SR":
        raise ExtractException("DICOM is an SR (structured report)")
    return values


class XNATFileMatch(FileMatch):
    """
    Sublass of FileMatch which provides getters and setters for xnat-specific
    metadata.
    """

    # def load_dicom(self):
    #     """
    #     Utility method used to load the dicom metadata for an umatched file
    #     when debugging
    #     """
    #     dicom_values = self.matcher.read_dicom(self.file)
    #     if dicom_values is not None:
    #         self.dicom_values = dicom_values
    #         self._columns = None

    @property
    def subject(self):
        return self.get("Subject", None)

    @property
    def session(self):
        return self.get("Session", None)

    @property
    def dataset(self):
        return self.get("Dataset", None)

    @property
    def study_date(self):
        return self.get("DICOM:StudyDate", None)

    @property
    def modality(self):
        return self.get("DICOM:Modality", None)

    @property
    def manufacturer(self):
        return self.get("DICOM:Manufacturer", None)

    @property
    def model(self):
        return self.get("DICOM:ManufacturerModelName", None)
