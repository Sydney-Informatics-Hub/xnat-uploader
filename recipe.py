import re


class RecipeException(Exception):
    pass


def parse_recipe(recipe):
    """
    Parse a recipe string and return a regular expression which matches the
    recipe.

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

    This function converts a recipe into a regexp object with named group
    parameters. This can be used to match target strings and return the
    desired dict with the match.groupdict() function

    Parameter names which consist of one or more of the same character are
    converted into patterns which match that number of digits. All other
    parameter names are converted into a non-greedy match up to the next
    character after the parameter in the pattern, or the end of the recipe.

    A list of all the params is returned so that calling code can know what to
    expect from the pattern without having to run it or reparse the recipe.
    Params are listed in the order they appear in the pattern.

    ---
    recipe (str): a recipe as described abov

    Returns: list of str, re.Pattern

    Raises: an re.error if for some reason the resulting regexp can't compile
    - for instance, if a parameter name has illegal characters or is repeated.
    """

    regexp = ""
    params = []
    for macro in re.finditer(r"{(.*?)}([^{]*)", recipe):
        param, delimiter = macro.group(1, 2)
        if param in params:
            raise RecipeException(f"Recipe has repeated parameter: {param}")
        if re.match(param[0] + "+$", param):
            regexp += f"(?P<{param}>" + (r"\d" * len(param)) + ")"
        else:
            if delimiter != "":
                c = delimiter[0]
                regexp += f"(?P<{param}>[^{c}]*?)"
            else:
                regexp += f"(?P<{param}>.*)"
        regexp += re.escape(delimiter)
        params.append(param)

    return params, re.compile(regexp)


def parse_recipes(recipe_config):
    """
    Parses a set of recipes from the config, keyed by label. The value for each
    label should be a list of recipe strings. The return value is the superset
    of all the parameters in all recipes, and a dict of list of re.Patterns by
    label.
    ---
    recipe_config: dict of { str: str }

    Returns: list of str, dict of { str: [ re.Pattern ] }
    """
    allparams = []
    recipes = {}
    for label, patterns in recipe_config.items():
        recipes[label] = []
        for pattern in patterns:
            params, pattern_re = parse_recipe(pattern)
            recipes[label].append(pattern_re)
            allparams += [p for p in params if p not in allparams]
    return allparams, recipes


def match_recipe(recipes, path):
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
    parts = path.parts
    if len(parts) < len(recipes):
        return None
    matchparts = parts[-len(recipes) :]
    values = {}
    for pattern in recipes:
        m = pattern.match(matchparts[0])
        if not m:
            return None
        for k, v in m.groupdict().items():
            values[k] = v
        matchparts = matchparts[1:]
    return values
