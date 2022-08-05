import re
import logging
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

XNAT_HIERARCHY = ["Subject", "Session", "Dataset"]
DICOM_PARAMS = ["Modality", "StudyDescription", "StudyDate"]

logger = logging.getLogger(__name__)


class RecipeException(Exception):
    pass


class Matcher:
    """
    A Matcher is a set of recipes for matching against filepaths and mappings
    which map the captured value to XNAT parameters. It's used to perform
    the matching, returning FileMatch objects, and also has methods which are
    used to get headers for the spreadsheets (since these will vary according
    to the parameters captured in the recipes)
    """

    def __init__(self, config):
        """
        config: dict with "paths" and "mappings"
        """
        self.parse_recipes(config["paths"])
        self.mappings = config["mappings"]
        self._headers = None
        self._dicom_params = set(DICOM_PARAMS)
        for k, vs in self.mappings.items():
            for v in vs:
                if v[:5] == "DICOM":
                    self._dicom_params.add(v[6:])
                elif v not in self.params:
                    raise Exception(
                        f"Value {v} in mapping for {k} not defined in a path"
                    )
        if set(self.mappings.keys()) != set(XNAT_HIERARCHY):
            raise Exception(f"Must have mappings for each of {XNAT_HIERARCHY}")

    @property
    def headers(self):
        if self._headers is None:
            self._headers = ["Pattern", "File", "Upload", "Status", "SessionLabel"]
            self._headers += XNAT_HIERARCHY + self.dicom_params + self.params
        return self._headers

    @property
    def dicom_params(self):
        return sorted(self._dicom_params)

    def parse_recipes(self, recipe_config):
        """
        Parses a set of recipes from the config, keyed by label. The value for
        each label should be a list of recipe strings. Builds the params
        variable, which is a list of all the params, and a list of compiled
        regular expressions.
        ---
        recipe_config: dict of { str: list of str  }
        """
        self.params = []
        self.recipes = {}
        for label, patterns in recipe_config.items():
            self.recipes[label] = []
            for pattern in patterns:
                params, regexp = self.parse_recipe(label, pattern)
                self.recipes[label].append(regexp)
                self.params += [p for p in params if p not in self.params]

    def parse_recipe(self, label, recipe):
        """
        Parse a recipe string and add it to the recipes dict, and add its
        params to self.params

        A recipe is a string with one or more parameter names between {}
        indicating parts of an input value (a filepath, for example) which we want
        to capture into those parameters. For example:

        "{SURNAME}-{GIVENNAME}-{YYYY}{MM}{DD}.txt"

        when matched against

        "Duck-Donald-19300831.txt"

        should return the dict

        {
                "SURNAME": "Duck",
                "GIVENNAME": "Donald",
                "YYYY":
                "1930",
                "MM": "08",
                "DD": "31"
        }

        Converts a recipe into a regexp object with named group
        parameters. This can be used to match target strings and return the
        desired dict with the match.groupdict() function

        Parameter names which consist of one or more of the same character are
        converted into patterns which match that number of digits. The
        parameter 'ID' matches a list of one or more consecutive digits.

        All other parameter names are converted into a non-greedy match up to
        the next character after the parameter in the pattern, or the end of
        the recipe.

        "*" and "**" are special recipes for matching and ignoring one or more
        than one intervening directories. They are returned as-is without being
        converted to a regexp.

        A list of all the params is returned so that calling code can know what to
        expect from the pattern without having to run it or reparse the recipe.
        Params are listed in the order they appear in the pattern.

        ---
        recipe (str): a recipe as described abov

        Returns: ( list of str, re.Pattern )

        Raises: an re.error if for some reason the resulting regexp can't compile
        - for instance, if a parameter name has illegal characters or is repeated.
        """

        regexp = ""
        params = []
        if recipe == "*" or recipe == "**":
            return [], recipe
        for macro in re.finditer(r"{(.*?)}([^{]*)", recipe):
            param, delimiter = macro.group(1, 2)
            if param in params:
                raise RecipeException(f"Recipe has repeated parameter: {param}")
            if re.match(param[0] + "+$", param):
                regexp += f"(?P<{param}>" + (r"\d" * len(param)) + ")"
            elif param == "ID":
                regexp += f"(?P<{param}>" + r"\d+" + ")"  # for Sublime Text
            else:
                if delimiter != "":
                    c = delimiter[0]
                    regexp += f"(?P<{param}>[^{c}]*?)"
                else:
                    regexp += f"(?P<{param}>.*)"
            regexp += re.escape(delimiter)
            params.append(param)
        return params, re.compile(regexp)

    def match_path(self, filepath):
        """
        Try to match a filepath against each of the recipes and return the label
        and values for the first one which matches.
        ---
        file: pathlib.Path

        returns: { str: str }
        """
        for label, recipes in self.recipes.items():
            values = self.match_recipe(recipes, filepath)
            if values:
                return label, values
        return None, None

    def match(self, filepath):
        """
        Calls match_path to get values from the filepath, and then tries to
        read DICOM values from the file itself. Returns a FileMatch object
        whether matching succeeds or fails - the success flag and values will
        be set if it succeeded.
        ---
        file: pathlib.Path

        returns: a FileMatch
        """
        label, values = self.match_path(filepath)
        if label:
            dicom_values = self.read_dicom(filepath)
            if dicom_values is None:
                match = FileMatch(self, filepath, None)
                match.status = "No DICOM metadata"
                return match
            return self.make_filematch(filepath, label, values, dicom_values)
        match = FileMatch(self, filepath, None)
        match.status = "unmatched"
        return match

    def make_filematch(self, file, label, path_values, dicom_values):
        """
        Map the values captured to XNAT hierarchy values and return an
        FileMatch object. If the mapping was unsuccessful, the FileMatch will
        have its success flag switched off
        """
        match = FileMatch(self, file, label)
        match.values = path_values
        match.dicom_values = dicom_values
        try:
            match.xnat_params = self.map_values(path_values, dicom_values)
            match.success = True
        except ValueError:
            match.success = False
            match.status = "unmatched"
        match.selected = match.success
        return match

    def from_spreadsheet(self, row):
        """
        Build a FileMatch from a spreadsheet row, using the FileMatch.from_row
        method
        """
        match = FileMatch(self, None, None)
        match.from_row(row)
        return match

    def match_recipe(self, patterns, path):
        """
        Attempt to match a pathlib.Path against a list of recipe patterns,
        returning the collected values if successful.

        The list of n recipes is matched against the last n parts of the path. For
        example, a recipe list equivalent to

        [ "{YYYY}-{MM}-{DD}", "{FILENAME}.txt" ]

        would successfully match the path

        "root" / "subdir" / "2022-05-24" / "myfile.txt"

        and return a dictionary with values for YYYY, MM, DD and FILENAME.

        If any recipes have overlapping parameters, the last value parse overwrites
        previous values.

        Values matching numeric patterns are not converted into numeric types.
        ---
        recipes: list of re.Pattern
        path: pathlib.Path

        Returns: None, or dict of { str: str }
        """
        dirs = list(path.parts)
        matchpatterns = patterns[:]
        values = {}
        while matchpatterns and dirs:
            pattern = matchpatterns[-1]
            if pattern == "*":
                matchpatterns.pop()
                dirs.pop()
            elif pattern == "**":
                if len(matchpatterns) > 1:
                    if matchpatterns[-2].match(dirs[-1]):
                        # if the next level up matches, stop chasing **
                        matchpatterns.pop()
                    else:
                        # otherwise, keep chasing the **
                        dirs.pop()
                else:
                    raise RecipeException("** at start of pattern")
            else:
                m = pattern.match(dirs[-1])
                if not m:
                    return None
                groups = m.groupdict()
                for k, v in groups.items():
                    values[k] = v
                matchpatterns.pop()
                dirs.pop()
        return values

    def read_dicom(self, file):
        """
        Try to parse the dicom metadata from the file and returns a dict
        of all the values extracted for this Matcher's dicom_params
        ---
        file: a pathlib.Path

        returns: { str: str }
        """
        try:
            dc_meta = dcmread(file)
            values = {p: dc_meta.get(p) for p in self._dicom_params}
            return values
        except InvalidDicomError:
            return None

    def map_values(self, path_values, dicom_values):
        """
        Given a dict of values which has been captured from a filepath by a recipe,
        try to map it to the XNAT hierarchy.

        Raises: ValueError if any of the required values are missing

        values: dict of { str: str }
        """
        for k, v in dicom_values.items():
            path_values["DICOM:" + k] = v
        xnat_params = {}
        for xnat_cat, path_vars in self.mappings.items():
            for v in path_vars:
                if v not in path_values:
                    raise ValueError(f"value {v} not found")
                if path_values[v] is None:
                    raise ValueError(f"value {v} is None")
            xnat_params[xnat_cat] = "".join([path_values[v] for v in path_vars])
        return xnat_params


class FileMatch:
    """
    Represents a file, which may or may not have been successfully matched.
    Used as the return value from Matcher.match and as the result of loading
    the log spreadsheet.
    """

    def __init__(self, matcher, file, label):
        self.matcher = matcher
        self.label = label
        self.file = str(file)
        self.values = None
        self.dicom_values = None
        self.xnat_params = None
        self.session_label = None
        self.error = None
        self.success = False
        self.status = None
        self.selected = None
        self._columns = None
        self._status = None
        self._selected = None

    @property
    def columns(self, refresh=False):
        """
        Returns this file's representation in the spreadsheet, which may or
        may not be a successful match
        """
        if self._columns is not None:
            return self._columns
        self._columns = [self.label, self.file]
        if self.selected:
            self._columns += ["Y"]
        else:
            self._columns += ["N"]
        if self.error is not None:
            self._columns += [self.error]
        else:
            if self.status is None:
                self._columns += [""]
            else:
                self._columns += [self.status]
        self._columns += [self.session_label]
        self._columns += self.dict_to_columns(XNAT_HIERARCHY, self.xnat_params)
        self._columns += self.dict_to_columns(
            self.matcher.dicom_params, self.dicom_values
        )
        self._columns += self.dict_to_columns(self.matcher.params, self.values)
        return self._columns

    def dict_to_columns(self, columns, values):
        if values is None:
            return ["" for _ in columns]
        else:
            return [values.get(c, "") for c in columns]

    def from_row(self, row):
        """
        Read a row from the spreadsheet and populate the values required to
        upload.
        """
        self.label = row[0]
        self.file = row[1]
        self.selected = row[2] == "Y"
        self.status = row[3]
        self.session_label = row[4]
        self.xnat_params = {
            "Subject": row[5],
            "Session": row[6],
            "Dataset": row[7],
        }
        self.dicom_values = {}
        c = 8
        for p in self.matcher.dicom_params:
            self.dicom_values[p] = row[c]
            c += 1
        self.values = {}
        for p in self.matcher.params:
            self.values[p] = row[c]
            c += 1

    def load_dicom(self):
        """
        Utility method used to load the dicom metadata for an umatched file
        when debugging
        """
        dicom_values = self.matcher.read_dicom(self.file)
        if dicom_values is not None:
            self.dicom_values = dicom_values
            self._columns = None

    @property
    def subject(self):
        if self.xnat_params is not None:
            return self.xnat_params["Subject"]
        else:
            return None

    @property
    def session(self):
        if self.xnat_params is not None:
            return self.xnat_params["Session"]
        else:
            return None

    @property
    def dataset(self):
        if self.xnat_params is not None:
            return self.xnat_params["Dataset"]
        else:
            return None

    @property
    def study_date(self):
        if self.session is not None:
            return self.session
        if self.dicom_values is not None:
            return self.dicom_values["StudyDate"]
        return ""

    @property
    def modality(self):
        if self.dicom_values is not None:
            return self.dicom_values["Modality"]
        else:
            return "OT"  # DICOM code for "Other"
