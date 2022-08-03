# import xnatutils
import xnatuploader.put


class Upload:
    """
    An Upload represents a session for a single patient and visit, which may
    have more than one file. All of the files are uploaded in a single call
    to xnatutils.put, which is called in Upload.upload
    """

    def __init__(self, session_label, subject, modality, scan_type):
        self.session_label = session_label
        self.subject = subject
        self.modality = modality
        self.scan_type = scan_type
        self.files = []

    def add_file(self, file):
        self.files.append(file)

    def upload(self, xnat_session, project, overwrite=False):
        """
        Upload one or more files to XNAT
        ---
        xnat_session: an XnatPy session, as returned by xnatutils.base.connect
        project: the XNAT project id to which we're uploading
        overwrite: Boolean
        """
        xnatuploader.put.put(
            self.session_label,
            self.scan_type,
            [mf.file for mf in self.files],
            resource_name="DICOM",
            project_id=project,
            subject_id=self.subject,
            modality=self.modality,
            create_session=True,
            connection=xnat_session,
            overwrite=overwrite,
        )

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
