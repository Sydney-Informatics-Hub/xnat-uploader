# iterate over the spreadsheet from AILDR and try to identify filename
# collisions (ie where the same filenames are duplicated in a session label)


from openpyxl import load_workbook


EXCELFILE = "aildr.xlsx"

wb = load_workbook(EXCELFILE)
ws = wb["Files"]

sessions = {}

for row in ws.rows:
    session_label = row[8].value
    scan_id = row[12].value
    filename = row[2].value
    if session_label not in sessions:
        sessions[session_label] = []
    if filename in sessions[session_label]:
        print(f"DUPLICATE {session_label} {scan_id} {filename}")
    else:
        sessions[session_label].append(filename)
