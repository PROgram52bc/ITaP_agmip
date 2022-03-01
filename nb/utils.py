from os import listdir
from os.path import isfile, isdir, join
import ipywidgets as widgets

def get_dir_content(dirpath):
    """ Get all files from a given directory.

    :dirpath: the path of the directory to be listed.
    :returns: a list of file names, empty if directory doesn't exist or there is no file in the directory.

    """
    return [f for f in listdir(dirpath) if isfile(join(dirpath, f))] if isdir(dirpath) else []

def displayable(prop, label=None):
    def f(prop):
        if label:
            print(f"{label}: {prop}")
        else:
            print(prop)
    return widgets.interactive_output(f, {"prop": prop})


def get_yield_variable(f):
    variables = [ key for key in f.variables.keys() if key.startswith("yield_") ]
    return next(iter(variables), None)

