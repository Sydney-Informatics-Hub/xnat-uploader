from xnatutils.base import connect
from xnatutils.exceptions import XnatUtilsError
import os.path
import xnat4tests

from medimages4tests.dicom.mri.fmap.ge.discovery_mr888.dv26_0_r05_2008a import (
    sample_image,
)

# This script will launch an xnat using xnat4tests, create a project called
# Test001, create a fake scan image with a couple of hundred dicoms, and upload
# them as a single patient session.

# Based on the code in xnatutils.put which I adapted for xnatuploader.put


def make_session(connection, session_cls, session, project_id, subject_id):
    """Creates a session (experiment) on the server and returns it as an
    object"""
    try:
        xproject = connection.projects[project_id]
    except KeyError:
        raise XnatUtilsError(f"Can't access project {project_id}")
    xsubject = connection.classes.SubjectData(label=subject_id, parent=xproject)
    xsession = session_cls(label=session, parent=xsubject)
    return xsession


def upload(**kwargs):
    """Uploads one or more files to a session specified by a
    project_id / subject_id / visit"""
    files = kwargs.pop("files", [])
    resource_name = kwargs.pop("resource_name", "DICOM")
    project_id = kwargs.pop("project_id", None)
    subject_id = kwargs.pop("subject_id", None)
    visit = kwargs.pop("visit", "1")
    modality = kwargs.pop("modality", "CT")
    overwrite = kwargs.pop("overwrite", False)
    session = f"{project_id}_{subject_id}_{visit}"
    with connect(**kwargs) as connection:
        modality = "MR"
        session_cls, scan_cls = get_xnat_classes(connection, modality)
        try:
            xsession = connection.experiments[session]
        except KeyError:
            xsession = make_session(
                connection, session_cls, session, project_id, subject_id
            )
        xdataset = scan_cls(id=modality, type=modality, parent=xsession)
        resource = None
        try:
            resource = xdataset.resources[resource_name]
        except KeyError:
            resource = xdataset.create_resource(resource_name)
        for file in files:
            fname = os.path.basename(file)
            if fname in resource.files:
                if overwrite:
                    resource.files[fname].delete()  # I am not sure if this is good
            resource.upload(file, fname)


def get_xnat_classes(connection, modality):
    """
    Tries to deduce the XNAT session and scan classes from the modality.
    If it doesn't work, falls back to MrSessionData and MrScanData
    --
    modality: str like "MR", "CT", "PET", etc
    returns: classes of session, scan
    """
    if modality == "MRPT":
        session_cls = connection.classes.PetmrSessionData
        scan_cls = connection.classes.MrScanData
    else:
        mcap = modality.capitalize()
        try:
            session_cls = getattr(connection.classes, mcap + "SessionData")
            scan_cls = getattr(connection.classes, mcap + "ScanData")
        except AttributeError:
            try:
                session_cls = connection.classes.MrSessionData
                scan_cls = connection.classes.MrScanData
            except AttributeError:
                # Old name < 1.8
                session_cls = connection.clases.mrSessionData
                scan_cls = connection.classes.mrScanData
    return session_cls, scan_cls


if __name__ == "__main__":
    xnat4tests.launch_xnat()
    xnat = xnat4tests.connect()
    project_id = "Test001"
    project = xnat.classes.ProjectData(parent=xnat, name=project_id)

    dicom_dir = sample_image()
    files = [str(f) for f in dicom_dir.glob("*.dcm")]

    upload(
        files=files,
        project_id=project_id,
        subject_id="123456",
        visit="1",
        modality="MR",
        resource_name="DICOM",
        connection=xnat,
    )
