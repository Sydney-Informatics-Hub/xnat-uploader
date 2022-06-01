def test_upload_one(xnat_project):
    xnat, project = xnat_project
    subject = xnat.classes.SubjectData(parent=project, label="test_subject")
    assert subject is not None
