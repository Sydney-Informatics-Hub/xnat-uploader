import re
import logging


logger = logging.getLogger(__name__)

# TODO- what to do about the DICOM:StudyDate v StudyDate stuff? I want to keep
# the DICOM prefixes so that the user's spreadsheets still work - maybe handle
# this in the subclass?


class FileMatch(dict):
    """
    Represents a file, which may or may not have been successfully matched.
    The values collected from paths and metadata extraction, and the metadata
    parameters mapped form them, are available as dict lookups, like
    filematch["Subject"].
    """

    def __init__(self, matcher, file=None, label=None, values=None):
        self.matcher = matcher
        self.label = label
        self.file = str(file)
        self.filename = None
        if file is not None:
            self.filename = file.name
        self.error = None
        self.success = False
        self.status = None
        self.selected = None
        self._columns = None
        if values is not None:
            for field, value in values.items():
                self[field] = value

    @property
    def columns(self):
        """
        Returns this file's representation in the spreadsheet, which may or
        may not be a successful match.

        fields: [ str ]
        """
        if self._columns is not None:
            return self._columns
        self._columns = [self.label, self.file, self.filename]
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
        self._columns += [self.get(v) for v in self.matcher.headers[5:]]
        return self._columns

    def from_row(self, row):
        """
        Read a row from a spreadsheet and populate the values required to
        upload.
        """
        self.label = row[0]
        self.file = row[1]
        self.filename = row[2]
        self.selected = row[3] == "Y"
        self.status = row[4]
        for field, value in zip(self.matcher.headers[5:], row[5:]):
            self[field] = value


class RecipeException(Exception):
    pass


class ExtractException(Exception):
    pass


class Matcher:
    """
    A Matcher is a set of patterns for matching against filepaths and mappings
    which map the captured value to field values. It's used to perform
    the matching, returning FileMatch objects.

    file_extractor is a function which does application-specific metadata
    extraction: it's up to the calling code to make sure that the values it
    sets are coordinated with the values extracted by the patterns and mappings

    extractor_options is application-specific config which is passed to
    file_extractor along with the filepath, if there's a need to skip certain
    files at this stage based on a config setting
    """

    def __init__(
        self,
        patterns,
        mappings,
        fields,
        file_extractor=None,
        extractor_options=None,
        match_class=FileMatch,
        loglevel="WARNING",
    ):
        """
        patterns: OrderedDict(str: str) of path patterns
        mappings: OrderedDict(str: str) of metadata values to captured fields
        fields: list of extra fields to include in the spreadsheet
        file_extractor: fn or None
        log_level: str
        """
        logger.setLevel(loglevel)
        logch = logging.StreamHandler()
        logch.setLevel(loglevel.upper())
        logger.addHandler(logch)
        self.mappings = mappings
        self.file_extractor = file_extractor
        self.extractor_options = extractor_options
        self.match_class = match_class
        self.fields = fields
        self._headers = None
        self.path_values = []
        self.parse_recipes(patterns)

    @property
    def headers(self):
        if self._headers is None:
            self._headers = [
                "Pattern",
                "File",
                "Filename",
                "Upload",
                "Status",
            ]
            self._headers += list(self.mappings.keys())
            self._headers += self.fields + self.path_values
        return self._headers

    def make_filematch(self, file, label=None, values=None):
        """
        Map a dict of values (which will be captured from the paths or by
        specialised metadata extraction) to metadata paramers and use
        those to populate a FileMatch object.
        If the mapping was unsuccessful, the FileMatch will have its success
        flag switched off.
        """
        match = self.match_class(self, file, label, values)
        try:
            for field, value in self.map_values(values).items():
                match[field] = value
            match.success = True
        except ValueError as e:
            logger.warning(f"Mapping error: {e}")
            match.success = False
            match.status = "unmatched"
        match.selected = match.success
        return match

    def map_values(self, values):
        """
        Given a dict of values which has been captured from a filepath by a
        pattern, returns the top-level metadata as defined by self.mappings

        Raises: ValueError if any of the required values are missing

        values: dict of { str: str }
        --
        returns: { str: str }
        """
        metadata = {}
        for field, path_vars in self.mappings.items():
            for v in path_vars:
                if v not in values:
                    raise ValueError(f"value {v} not found")
                if values[v] is None:
                    raise ValueError(f"value {v} is None")
            metadata[field] = "".join([values[v] for v in path_vars])
            metadata[field] = metadata[field].replace(" ", "_")
        return metadata

    def from_spreadsheet(self, row):
        """
        Build a FileMatch from a spreadsheet row, using the FileMatch.from_row
        method
        """
        match = self.match_class(self)
        match.from_row(row)
        return match

    def parse_recipes(self, recipe_config):
        """
        Parses a set of recipes from the config, keyed by label. The value for
        each label should be a list of recipe strings. Builds the params
        variable, which is a list of all the params, and a list of compiled
        regular expressions.
        ---
        recipe_config: dict of { str: list of str  }
        """
        self.recipes = {}
        for label, patterns in recipe_config.items():
            self.recipes[label] = []
            for pattern in patterns:
                path_values, regexp = self.parse_recipe(label, pattern)
                self.recipes[label].append(regexp)
                self.path_values += [
                    p for p in path_values if p not in self.path_values
                ]

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
            else:
                regexp += f"(?P<{param}>.*)"
            regexp += re.escape(delimiter)
            params.append(param)
        return params, re.compile(regexp)

    def match(self, root, filepath):
        """
        Calls match_path to get values from the filepath, and then tries to
        read DICOM values from the file itself. Returns a FileMatch object
        whether matching succeeds or fails - the success flag and values will
        be set if it succeeded.
        ---
        file: pathlib.Path

        returns: a FileMatch
        """
        label, values = self.match_path(filepath.relative_to(root))
        if label:
            if self.file_extractor is not None:
                try:
                    file_values = self.file_extractor(
                        filepath,
                        self.extractor_options,
                    )
                except ExtractException as e:
                    match = self.match_class(self, filepath)
                    match.status = "unmatched"
                    match.error = str(e)
                    return match
                for field, value in file_values.items():
                    values[field] = value  # file metadata can overwrite path
            return self.make_filematch(filepath, label, values)
        match = self.match_class(self, filepath)
        match.status = "unmatched"
        return match

    def match_path(self, filepath):
        """
        Try to match a filepath against each of the recipes and return the label
        and values for the first one which matches.
        ---
        file: pathlib.Path

        returns: { str: str }
        """
        logger.debug(f"Trying to match {filepath}")
        for label, recipes in self.recipes.items():
            logger.debug(f"> pattern: {label}")
            values = self.match_recipe(recipes, filepath)
            if values:
                logger.debug(f"> successful path match for {label}")
                return label, values
        return None, None

    def match_recipe(self, patterns, path):
        """
        Matches a list of patterns against a pathlib.Path, returning None if
        no match was possible, or a dict of captured values.

        Matching starts from the beginning and works down the subdirectories
        by the following rules:

        - if the next subdir matches the next pattern, capture any values and
          move to the next subdir and pattern

        - if the pattern is "*", match it against any subdir and keep going

        - if the pattern is "**", match it against one or more subdirs until
          the rest of the path matches the rest of the patterns (a
          "non-greedy" match in regexp terms)

        Both "*" and "**" must match against at least one subdir.

        ---
        patterns: list of re.Pattern
        path: pathlib.Path

        Returns: None, or dict of { str: str }
        """
        dirs = list(path.parts)
        matchpatterns = patterns[:]
        values = self.match_recipe_r(matchpatterns, dirs)
        return values

    def match_recipe_r(self, patterns, dirs):
        """The recursive part of match_recipe. Checks if the head of patterns
        matches the head of dirs, returning None if there's no match or either
        patterns or dirs is exhausted early, and adds any captured values to
        values captured further down the list. Uses lookahead on '**' to see
        if the rest of the pattern after this dir matches. Won't be efficient
        on very deep hierarchies because of this.

        patterns: list of re.Pattern
        path: list of str

        Returns: None, or dict of { str: str }
        """

        if not patterns:
            if dirs:
                logger.debug(">> ran out of patterns before end of path")
                return None
            else:
                return {}  # reached the end of both at the same time
        if not dirs:
            logger.debug(">> ran out of path before end of patterns")
            return None
        values = {}
        tail_values = self.match_recipe_r(patterns[1:], dirs[1:])
        if patterns[0] == "**":
            logger.debug(f">> pattern ** / path {dirs[0]}")
            if tail_values is not None:
                logger.debug(">> Matched remainder of path")
                return tail_values
            logger.debug(">> moving to next path")
            return self.match_recipe_r(patterns, dirs[1:])
        if patterns[0] == "*":
            logger.debug(f">> pattern * / path {dirs[0]}")
            return tail_values
        logger.debug(f">> pattern {patterns[0]} / path {dirs[0]}")
        m = patterns[0].match(dirs[0])
        if not m:
            logger.debug(">> No match")
            return None
        values = m.groupdict()
        if tail_values is None:
            logger.debug(">> Match but no values")
            return None
        for k, v in tail_values.items():
            values[k] = v
            logger.debug(f">> Matched values {values}")
        return values

    def match_paths(self, patterns, dirs):
        """
        Given a list of patterns and path parts, this tries to match
        the first pattern with the first path. If there's only one
        pattern, it adds the extra condition that there must be only one
        path - this is so that the last pattern in a recipe will only
        match a file, not a directory
        """
        m = patterns[0].match(dirs[0])
        if m is not None:
            if len(patterns) > 1:
                return m
            if len(dirs) == 1:
                return m
        return None
