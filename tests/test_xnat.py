from xnat4tests import launch_xnat, stop_xnat, connect, config
import pytest


@pytest.mark.skip(reason="not there yet")
def test_basic_xnat():
    launch_xnat()

    # Run your tests
    with connect() as login:
        PROJECT = "MYPROJECT"
        SUBJECT = "MYSUBJECT"
        SESSION = "MYSESSION"

        login.put("/data/archive/projects/MY_TEST_PROJECT")

        # Create subject
        xsubject = login.classes.SubjectData(
            label=SUBJECT, parent=login.projects[PROJECT]
        )
        # Create session
        login.classes.MrSessionData(label=SESSION, parent=xsubject)

    assert [p.name for p in (config.XNAT_ROOT_DIR / "archive").iterdir()] == [PROJECT]

    # Remove the container after you are done (not strictly necessary)
    stop_xnat()
