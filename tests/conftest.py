import xnat4tests
import pytest


@pytest.fixture(scope="session")
def xnat_project():
    xnat4tests.launch_xnat()
    xnat = xnat4tests.connect()
    project = xnat.classes.ProjectData(parent=xnat, label="Test")
    yield xnat, project
    xnat4tests.stop_xnat()
