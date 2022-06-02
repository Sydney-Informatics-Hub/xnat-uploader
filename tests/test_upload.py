import xnatutils
from pathlib import Path

FIXTURES_DIR = Path("tests/fixtures")
DICOM = FIXTURES_DIR / "sample_dicoms" / "image-00000.dcm"
SESSION_ID = "SESSION01"
DATASET_ID = "DATASET01"
# XNAT : Project / Subject / Session


def test_upload_one(xnat_project):
    xnat, project = xnat_project
    subject = xnat.classes.SubjectData(parent=project, label="subject001")
    assert subject is not None
    xnatutils.put(
        SESSION_ID,
        DATASET_ID,
        [str(DICOM)],
        project_id=project.name,
        subject_id="subject001",
        create_session=True,
        connection=xnat,
    )
    sessions = xnatutils.ls(project_id="Test001", datatype="session", connection=xnat)
    print(f"Sessions: {sessions}")
    assert sessions is not None
    assert len(sessions) == 1
    session = sessions[0]
    assert session == SESSION_ID
    scans = xnatutils.ls(xnat_id=session, datatype="scan", connection=xnat)
    assert scans is not None
    assert len(scans) == 1
