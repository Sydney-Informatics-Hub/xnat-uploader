import xnat4tests

PROJECT_ID = "Test001"

xnat4tests.start_xnat()

xnat_connection = xnat4tests.connect()

project = xnat_connection.classes.ProjectData(
    parent=xnat_connection,
    name=PROJECT_ID,
)

print(f"Launched xnat with project {PROJECT_ID}")
