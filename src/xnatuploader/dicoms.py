import logging
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from xnatuploader.matcher import ExtractException, FileMatch

DICOM_PARAMS = [
    "Modality",
    "SeriesNumber",
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
    "DICOM:SeriesNumber",
    "DICOM:StationName",
    "DICOM:StudyDate",
    "DICOM:StudyDescription",
]

logger = logging.getLogger(__name__)


def dicom_extractor(file, options):
    """
    Try to extract DICOM metadata from a file, and check that it doesn't
    have an encapsulated document, or is of modality SR (which is a special
    type reserved for reports).

    Raises ExtractException if the file is not a DICOM, has an embedded
    report or the wrong modality, or one of skip_image_types - this is passed
    in so that it can be controlled by configuration rather than hard-coded
    ---
    file: pathlib.Path
    options: { str: [ str ]}

    returns: {str: str}

    raises: ExtractException
    """
    values = None
    dc_meta = None
    try:
        dc_meta = dcmread(file)
    except InvalidDicomError:
        raise ExtractException("File is not a DICOM")
    if dc_meta.get("EncapsulatedDocument"):
        raise ExtractException("DICOM is an encapsulated report")
    values = {f"DICOM:{p}": dc_meta.get(p) for p in DICOM_PARAMS}
    if "DICOM:Modality" not in values:
        raise ExtractException("DICOM has no modality")
    if values["DICOM:Modality"] == "SR":
        raise ExtractException("DICOM is an SR (structured report)")
    image_type = dc_meta.get("ImageType")
    if "skip_image_types" in options and image_type:
        if image_type[2] in options["skip_image_types"]:
            raise ExtractException(f"DICOM has banned image type '{image_type[2]}'")
    return values


class XNATFileMatch(FileMatch):
    """
    Sublass of FileMatch which provides getters and setters for xnat-specific
    metadata.
    """

    def load_dicom(self, options):
        """
        Utility method used to load the dicom metadata for an umatched file
        so that it can be written to the spreadsheet
        """
        try:
            dicom_values = dicom_extractor(self.file, options)
            if dicom_values is not None:
                for key, value in dicom_values.items():
                    self[key] = value
        except ExtractException as e:
            logger.debug(f"DICOM extraction failed: {e}")

    # session_label gets constructed by the calling code in xnatuploader,
    # so it gets a setter as well as a getter

    @property
    def session_label(self):
        return self.get("SessionLabel", None)

    @session_label.setter
    def session_label(self, value):
        self["SessionLabel"] = value

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
    def series_number(self):
        return self.get("DICOM:SeriesNumber", None)

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
