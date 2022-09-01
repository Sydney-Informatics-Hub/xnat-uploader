import hashlib
from xnatutils.base import (
    sanitize_re,
    illegal_scan_chars_re,
    get_resource_name,
    session_modality_re,
    connect,
)
from xnatutils.exceptions import (
    XnatUtilsUsageError,
    XnatUtilsError,
    XnatUtilsDigestCheckFailedError,
    XnatUtilsNoMatchingSessionsException,
)

HASH_CHUNK_SIZE = 2**20

# My version of put with session and scan class fix


def resource(session, scan, *filenames, **kwargs):
    """
    Uploads datasets to an XNAT instance project (requires manager privileges for the
    project).

    The format of the uploaded file is guessed from the file extension
    (recognised extensions are '.nii', '.nii.gz', '.mif'), the scan entry is
    created in the session and if 'create_session' kwarg is True the
    subject and session are created if they are not already present, e.g.

        >>> xnatutils.put('TEST001_001_MR01', 'a_dataset', ['test.nii.gz'],
                          create_session=True)

    NB: If the scan already exists the 'overwrite' kwarg must be provided to
    overwrite it.

    User credentials can be stored in a ~/.netrc file so that they don't need
    to be entered each time a command is run. If a new user provided or netrc
    doesn't exist the tool will ask whether to create a ~/.netrc file with the
    given credentials.

    Parameters
    ----------
    session : str
        Name of the session to upload the dataset to
    scan : str
        Name for the dataset on XNAT
    filenames : list(str)
        Filenames of the dataset(s) to upload to XNAT or a directory containing
        the datasets.
    overwrite : bool
        Allow overwrite of existing dataset
    create_session : bool
        Create the required session on XNAT to upload the the dataset to
    resource_name : str
        The name of the resource (the data format) to
        upload the dataset to. If not provided the format
        will be determined from the file extension (i.e.
        in most cases it won't be necessary to specify
    project_id : str
        The ID of the project to upload the dataset to
    subject_id : str
        The ID of the subject to upload the dataset to
    scan_id : str
        The ID for the scan (defaults to the scan type)
    modality : str
        The modality of the session to upload
    user : str
        The user to connect to the server with
    loglevel : str
        The logging level to display. In order of increasing verbosity
        ERROR, WARNING, INFO, DEBUG.
    connection : xnat.Session
        An existing XnatPy session that is to be reused instead of
        creating a new session. The session is wrapped in a dummy class
        that disables the disconnection on exit, to allow the method to
        be nested in a wider connection context (i.e. reuse the same
        connection between commands).
    server : str | int | None
        URI of the XNAT server to connect to. If not provided connect
        will look inside the ~/.netrc file to get a list of saved
        servers. If there is more than one, then they can be selected
        by passing an index corresponding to the order they are listed
        in the .netrc
    use_netrc : bool
        Whether to load and save user credentials from netrc file
        located at $HOME/.netrc
    """
    # Set defaults for kwargs
    create_session = kwargs.pop(
        "create_session",
        False,
    )
    resource_name = kwargs.pop("resource_name", None)
    project_id = kwargs.pop("project_id", None)
    subject_id = kwargs.pop("subject_id", None)
    scan_id = kwargs.pop("scan_id", None)
    modality = kwargs.pop("modality", None)
    if sanitize_re.match(session):
        raise XnatUtilsUsageError(
            "Session '{}' is not a valid session name (must only contain "
            "alpha-numeric characters and underscores)".format(session)
        )
    if illegal_scan_chars_re.search(scan) is not None:
        raise XnatUtilsUsageError(
            "Scan name '{}' contains illegal characters".format(scan)
        )

    if resource_name is None:
        if len(filenames) == 1:
            resource_name = get_resource_name(filenames[0])
        else:
            raise XnatUtilsUsageError(
                "'resource_name' option needs to be provided when uploading "
                "multiple files"
            )
    else:
        resource_name = resource_name.upper()
    with connect(**kwargs) as login:
        if modality is None:
            match = session_modality_re.match(session)
            if match is None:
                modality = "MR"  # The default
            else:
                modality = match.group(1)
        session_cls, scan_cls = get_xnat_classes(login, modality)
        try:
            xsession = login.experiments[session]
        except KeyError:
            if create_session:
                if project_id is None and subject_id is None:
                    try:
                        project_id, subject_id, _ = session.split("_")
                    except ValueError:
                        raise XnatUtilsUsageError(
                            "Must explicitly provide project and subject IDs "
                            "if session ID ({}) scheme doesn't match "
                            "<project>_<subject>_<visit> convention, i.e. "
                            "have exactly 2 underscores".format(session)
                        )
                if project_id is None:
                    project_id = session.split("_")[0]
                if subject_id is None:
                    subject_id = "_".join(session.split("_")[:2])
                try:
                    xproject = login.projects[project_id]
                except KeyError:
                    raise XnatUtilsUsageError(
                        "Cannot create session '{}' as '{}' does not exist "
                        "(or you don't have access to it)".format(session, project_id)
                    )
                # Creates a corresponding subject and session if they don't
                # exist
                xsubject = login.classes.SubjectData(label=subject_id, parent=xproject)
                xsession = session_cls(label=session, parent=xsubject)
            else:
                raise XnatUtilsNoMatchingSessionsException(
                    "'{}' session does not exist, to automatically create it "
                    "please use '--create_session' option.".format(session)
                )
        xdataset = scan_cls(
            id=(scan_id if scan_id is not None else scan), type=scan, parent=xsession
        )
        resource = None
        # get the existing resource, if there is one
        # this means that we can reconnect to a resource and add files to it
        # after being interrupted
        try:
            resource = xdataset.resources[resource_name]
        except KeyError:
            resource = xdataset.create_resource(resource_name)
        return resource


def get_xnat_classes(login, modality):
    """
    Tries to deduce the XNAT session and scan classes from the modality.
    If it doesn't work, falls back to MrSessionData and MrScanData
    --
    modality: str like "MR", "CT", "PET", etc
    returns: classes of session, scan
    """
    if modality == "MRPT":
        session_cls = login.classes.PetmrSessionData
        scan_cls = login.classes.MrScanData
    else:
        mcap = modality.capitalize()
        try:
            session_cls = getattr(login.classes, mcap + "SessionData")
            scan_cls = getattr(login.classes, mcap + "ScanData")
        except AttributeError:
            try:
                session_cls = login.classes.MrSessionData
                scan_cls = login.classes.MrScanData
            except AttributeError:
                # Old name < 1.8
                session_cls = login.clases.mrSessionData
                scan_cls = login.classes.mrScanData
    return session_cls, scan_cls


def calculate_checksum(fname):
    try:
        file_hash = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except OSError:
        raise XnatUtilsDigestCheckFailedError(
            "Could not check digest of '{}' ".format(fname)
        )


def get_digests(resource):
    """
    Downloads the MD5 digests associated with the files in a resource.
    These are saved with the downloaded files in the cache and used to
    check if the files have been updated on the server
    """
    result = resource.xnat_session.get(resource.uri + "/files")
    if result.status_code != 200:
        raise XnatUtilsError(
            "Could not download metadata for resource {}. Files "
            "may have been uploaded but cannot check checksums".format(resource.id)
        )
    return dict((r["Name"], r["digest"]) for r in result.json()["ResultSet"]["Result"])
