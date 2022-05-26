# Don't quite understand how to get from the xnat_session to the xnat utils
# stuff


def test_upload_one(xnat_session):
    project = xnat_session.classes.ProjectData(parent=xnat_session, label="testing")
    subject = xnat_session.classes.SubjectData(parent=project, label="test_subject")
    assert subject is not None
