import xnat4tests
import pytest
from pathlib import Path


@pytest.fixture
def test_files():
    fixtures_dir = Path("tests") / "fixtures"
    return {
        "config_excel": fixtures_dir / "template.xlsx",
        "config": fixtures_dir / "recipe-xnat.json",
        "source": fixtures_dir / "source",
        "log": fixtures_dir / "log.xlsx",
    }


@pytest.fixture(scope="session")
def xnat_project():
    xnat4tests.launch_xnat()
    xnat = xnat4tests.connect()
    project = xnat.classes.ProjectData(parent=xnat, name="Test001")
    yield xnat, project
    xnat4tests.stop_xnat()
