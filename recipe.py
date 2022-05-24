
import re, json

def parse_recipe(recipe):
	"""Converts a recipe pattern into a regular expression and list of
	variable names. Works as follows:

	{A} {NN} {MM} {YYYY} -> a pattern which matches n digits
	{ANY_OTHER_STRING} -> a pattern which does a non-greedy match to the next
	                      character after the pattern

	returns a regular expression with (?P<name>..) groups for each of the
	patterns.

	"""


	regexp = ''
	for macro in re.finditer(r'{(.*?)}([^{]*)', recipe):
		var, delimiter = macro.group(1, 2)
		if re.match(var[0] + '+$', var):
			regexp += f'(?P<{var}>' + (r'\d' * len(var)) + ')'
		else:
			if delimiter != "":
				c = delimiter[0]
				regexp += f'(?P<{var}>[^{c}]*?)'
			else:
				regexp += f'(?P<{var}>.*)'
		regexp += re.escape(delimiter)
	return re.compile(regexp)


def load_recipes(recipe_json):
	"""Reads in a JSON file associating labels with recipes, and returns
	a dict of re objects keyed by labels
	"""
	with open(recipe_json, "r") as rfh:
		recipes = json.load(rfh)
		for label, patterns in recipes.items():
			recipes[label] = [ parse_recipe(pattern) for pattern in patterns ]
	return recipes

def match_recipe(recipe, parts):
	""" given a list of patterns and a filepath, see if they match, 
	starting from the end

	ie if the path is [ dir1, dir2, dir3, dir4, file ]

	and the recipe is [ pat1, pat2, pat3 ]

	then try to match file -> pat3, dir4 -> pat2 and dir3 -> pat1

	TODO: explain this better!
	"""
	if len(parts) < len(recipe):
		print(f"Fewer parts {parts} than recipe {recipe}")
		return None
	matchparts = parts[-len(recipe):]
	values = {}
	for pattern in recipe:
		m = pattern.match(matchparts[0])
		if not m:
			return None
		for k, v in m.groupdict().items():
			values[k] = v
		matchparts = matchparts[1:]
	return values