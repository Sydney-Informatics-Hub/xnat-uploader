from openpyxl import Workbook, load_workbook
from openpyxl.styles.alignment import Alignment

FILE_COLUMN_WIDTH = 50
HELP_COLUMN_WIDTH = 25
HELP_ROW_HEIGHT = 90

HELP_TEXT = """
Paths are a set of patterns to be matched against file paths in the source directory.
Values in curly brackets like {SubjectName} are captured into variables.
Variables with names in all caps like {YYYY} will only match numbers.
Mappings are used to combine the variables captured from a path to the
XNAT hierarchy Subject / Session / Dataset.

XNAT configures the XNAT project and server.
"""


class WorkbookError(Exception):
    pass


def new_workbook(file):
    """
    Make a new spreadsheet with the instructions worksheet and default
    patterns
    --
    file: filepath.Path
    """
    wb = Workbook()
    ws = wb.active
    for col in "ABCDE":
        ws.column_dimensions[col].width = HELP_COLUMN_WIDTH

    ws.title = "Configuration"
    ws["A1"] = "Instructions"
    ws["A2"] = HELP_TEXT
    ws["A2"].alignment = Alignment(wrapText=True)
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = HELP_ROW_HEIGHT
    ws["A4"] = "Configuration"
    ws["A5"] = "Paths"
    ws["B5"] = "DICOM"
    ws["C5"] = "{SubjectName}-{SubjectId}"
    ws["D5"] = "{YYYY}{MM}{DD}-{Label}.dcm"
    ws["A10"] = "Mappings"
    ws["B10"] = "Subject"
    ws["C10"] = "SubjectId"
    ws["B11"] = "Session"
    ws["C11"] = "YYYY"
    ws["D11"] = "MM"
    ws["E11"] = "DD"
    ws["B12"] = "Dataset"
    ws["C12"] = "Label"
    ws["A14"] = "XNAT"
    ws["B14"] = "Project"
    ws["C14"] = "Test01"
    ws["B15"] = "Server"
    ws["C15"] = "http://localhost:8080"
    wb.save(file)


def add_filesheet(wb, matcher):
    """
    Adds a worksheet to a workbook with headers from the matcher object
    and niceties such as a wider column for the file names
    ---
    wb: a Workbook
    matcher: a Matcher

    returns: the new worksheet
    """
    if "Files" in wb:
        old_files = wb["Files"]
        old_files.title = "Files-prev"  # will get 1, 2, etc appended if exists
    ws = wb.create_sheet("Files")
    ws.column_dimensions["B"].width = FILE_COLUMN_WIDTH
    ws.append(matcher.headers)
    return ws


def load_config(excelfile):
    wb = load_workbook(excelfile)
    if "Configuration" not in wb:
        raise WorkbookError(f"No worksheet named 'Configuration' in {excelfile}")
    ws = wb["Configuration"]
    config = {}
    section = None
    sections = ["paths", "mappings", "xnat"]
    for row in ws:
        if row[0].value is not None:
            section = row[0].value.lower()
        var = row[1].value
        if var is not None and section is not None:
            if section not in config:
                config[section] = {}
            cells = [cell.value for cell in row[2:] if cell.value is not None]
            if section == "xnat":
                config[section][var] = cells[0]
            else:
                config[section][var] = cells
    missing = [s for s in sections if s not in config]
    if len(missing) > 0:
        raise WorkbookError(f"Missing config sections: {missing}")
    return config
