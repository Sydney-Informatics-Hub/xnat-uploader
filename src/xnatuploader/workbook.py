from openpyxl import Workbook, load_workbook

FILE_COLUMN_WIDTH = 50


class WorkbookError(Exception):
    pass


def new_workbook(matcher):
    """
    Make a new openpyxl workbook with headers from the matcher object
    and niceties such as a wider column for the file names
    ---
    matcher: a Matcher
    returns: a Workbook
    """
    wb = Workbook()
    ws = wb.active
    ws.column_dimensions["B"].width = FILE_COLUMN_WIDTH
    ws.title = "Files"
    ws.append(matcher.headers)
    return wb


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
