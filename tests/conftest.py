import xnat4tests
import pytest


@pytest.fixture(scope="session")
def xnat_session():
    xnat4tests.launch_xnat()
    yield xnat4tests.connect()
    xnat4tests.stop_xnat()
