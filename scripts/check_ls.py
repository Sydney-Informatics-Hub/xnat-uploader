import xnatutils


scans = xnatutils.ls(
    "20190115",
    project_id="Test001",
    subject_id="397829",
    datatype="scan",
    return_attr="label",
    server="http://localhost:8080",
)

for scan in scans:
    print(scan)
