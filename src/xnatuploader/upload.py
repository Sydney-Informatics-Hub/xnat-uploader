# import xnatutils
import xnatuploader.put
import os.path
import logging

logger = logging.getLogger(__name__)


class Upload:
    """
    An Upload represents a session for a single patient and visit, which may
    have more than one file.
    """

    def __init__(self, session_label, subject, modality, scan_type):
        self.session_label = session_label
        self.subject = subject
        self.modality = modality
        self.scan_type = scan_type
        self.new_session = True
        self.xnat_session = None
        self.files = []

    def add_file(self, file):
        self.files.append(file)

    def start_upload(self, xnat_session, project):
        """Create a resource in the session for this scan"""
        self.xnat_session = xnat_session
        self.resource = xnatuploader.put.resource(
            self.session_label,
            self.scan_type,
            resource_name="DICOM",
            project_id=project,
            subject_id=self.subject,
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
            xnat_filename = os.path.basename(file.file).replace(" ", "%20")
            if xnat_filename not in digests:
                status[
                    file.file
                ] = f"File {file.file} {xnat_filename} not found in digests"
            else:
                remote_digest = digests[xnat_filename]
                local_digest = xnatuploader.put.calculate_checksum(file.file)
                if local_digest != remote_digest:
                    status[
                        file.file
                    ] = f"Digest mismatch {local_digest} {remote_digest}"
                else:
                    status[file.file] = "success"
        return status

    # def upload_all(self, xnat_session, project, overwrite=False):
    #     """
    #     Upload a file to XNAT
    #     ---
    #     xnat_session: an XnatPy session, as returned by xnatutils.base.connect
    #     project: the XNAT project id to which we're uploading
    #     overwrite: Boolean
    #     """
    #     xnatuploader.put.put(
    #         self.session_label,
    #         self.scan_type,
    #         [file.file for file in self.files],
    #         resource_name="DICOM",
    #         project_id=project,
    #         subject_id=self.subject,
    #         modality=self.modality,
    #         create_session=self.new_session,
    #         connection=xnat_session,
    #         overwrite=overwrite,
    #     )
    #     self.create_session = False  # don't try to recreate sessions

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
