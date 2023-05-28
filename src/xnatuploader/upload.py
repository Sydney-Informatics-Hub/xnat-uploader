import xnatuploader.put
import os.path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Upload:
    """
    An Upload represents a session for a single patient and visit, which may
    have more than one file.

    """

    session_label: str
    subject: str
    date: str
    modality: str
    series_number: str
    scan_type: str
    manufacturer: str
    model: str

    def __post_init__(self):
        self.new_session = True
        self.xnat_session = None
        self.files = []

    @property
    def label(self):
        """A value which can identify this upload in XNAT - scan_type
        corresponds to dataset. Used for logging upload errors which are
        triggered by start_upload below."""
        return f"{self.session_label}/{self.scan_type}"

    def add_file(self, file):
        """Add a file to this upload's file list. If the series number on the
        file doesn't match the upload series number, doesn't add it and
        logs an error"""
        if file.series_number == self.series_number:
            self.files.append(file)
            return True
        else:
            logger.error(
                f"""
{self.session_label} {file.filename} series number {file.series_number} does
not match series number in scan ({self.series_number})
"""
            )
            return False

    def start_upload(self, xnat_session, project):
        """Create a resource in the session for this scan"""
        self.xnat_session = xnat_session
        self.resource = xnatuploader.put.resource(
            self.session_label,
            self.scan_type,
            resource_name="DICOM",
            project_id=project,
            subject_id=self.subject,
            scan_id=self.series_number,
            #            date=self.date,
            modality=self.modality,
            create_session=self.new_session,
            connection=xnat_session,
        )

    def upload(self, files, overwrite=False):
        """
        Upload a batch of files to the current resource and checks their
        digests

        Args:
            files: list of Matchfile
            overwrite: boolean
        Returns:
            dict of { str: str } with a status message, "success" or an error
        ---
        """
        for file in files:
            fname = os.path.basename(file.file)
            if fname in self.resource.files:
                if overwrite:
                    self.resource.files[fname].delete()  # I am not sure if this is good
            self.resource.upload(file.file, fname)
        return self.check_digests(files)

    def check_digests(self, files):
        """Check the digests of a batch of files, and returns a hash-by-filename
        of success or failure
        """
        result = self.xnat_session.get(self.resource.uri + "/files")
        if result.status_code != 200:
            logger.error(
                f"Request for digests at {self.resource.uri} returned status {result.status_code}"
            )
            digests = {}
        else:
            digests = {
                f["Name"]: f["digest"] for f in result.json()["ResultSet"]["Result"]
            }
        status = {}
        for file in files:
            xnat_filename = os.path.basename(file.file)
            if xnat_filename not in digests:
                status[
                    file.file
                ] = f"File {file.file} {xnat_filename} not found in digests"
                logger.error(status[file.file])
                logger.error(digests)
            else:
                remote_digest = digests[xnat_filename]
                local_digest = xnatuploader.put.calculate_checksum(file.file)
                if local_digest != remote_digest:
                    status[
                        file.file
                    ] = f"Digest mismatch {local_digest} {remote_digest}"
                    logger.error(file.file + ": " + status[file.file])
                else:
                    status[file.file] = "success"
        return status

    def log(self, logger):
        """
        Write an upload batch to logger for debugging
        ---
        upload: a dict as returned by collate_upload
        """
        logger.info(f"Session: {self.session_label}")
        logger.info(f"    Subject: {self.upload}")
        logger.info(f"    Modality: {self.modality}")
        logger.info(f"    Scan type: {self.scan_type}")
        for file in self.files:
            logger.info(f"        File: {file.file}")


def trigger_pipelines(xnat_session, project, uploads):
    """
    Call the put API endpoints to trigger DICOM metadata extraction and
    snapshotting on the server
    """
    sessions = {upload.session_label: upload.subject for upload in uploads.values()}
    for session, subject in sessions.items():
        try:
            logger.debug(f"Pipelines for {project} / {subject} / {session}")
            uri = f"/data/projects/{project}/subjects/{subject}/experiments/{session}"
            xnat_session.put(f"{uri}?pullDataFromHeaders=true")
            xnat_session.put(f"{uri}?fixScanTypes=true")
            xnat_session.put(f"{uri}?triggerPipelines=true")
        except Exception as e:
            logger.info("Error while triggering metadata extraction / pipelines")
            logger.info(str(e))
