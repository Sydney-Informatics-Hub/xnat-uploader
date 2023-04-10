import logging
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from xnatuploader.matcher import ExtractException

DICOM_PARAMS = [
    "Modality",
    "StudyDescription",
    "StudyDate",
    "Manufacturer",
    "ManufacturerModelName",
    "StationName",
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
        values = {p: dc_meta.get(p) for p in DICOM_PARAMS}
    except InvalidDicomError:
        raise ExtractException("File is not a DICOM")
    if "EncapsulatedDocument" in values:
        raise ExtractException("DICOM has an encapsulated document")
    if "Modality" not in values:
        raise ExtractException("DICOM has no modality")
    if values["Modality"] == "SR":
        raise ExtractException("DICOM is an SR (structured report)")
    return values
