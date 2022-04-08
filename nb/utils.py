from os import listdir
from os.path import isfile, isdir, join, basename, splitext
import ipywidgets as widgets
import branca.colormap as cm
from statistics import quantiles
import re

# For DownloadButton
import base64
import hashlib
from typing import Callable
from IPython.display import HTML

def is_float(n):
    """check if number is float

    :n: The number to be checked
    :returns: Boolean

    """
    try:
        float(n)
        return True
    except (ValueError, TypeError):
        return False

def get_dir_content(dirpath):
    """ Get all files from a given directory.

    :dirpath: the path of the directory to be listed.
    :returns: a list of file names, empty if directory doesn't exist or there is no file in the directory.

    """
    return [f for f in listdir(dirpath) if isfile(join(dirpath, f))] if isdir(dirpath) else []

def get_file_content(filepath):
    with open(filepath, "rb") as f:
        return f.read()

def display_with_style(prop, label=None):
    """Display prop and label with styles
    """
    # TODO: add classes for styles <2022-03-31, David Deng> #
    if label:
        display(HTML(f"<p><b>{label}</b>: {prop}</p>"))
    else:
        display(HTML(f"<p>{prop}</p>"))

def displayable(prop, label=None):
    def f(prop):
        display_with_style(prop, label)
    return widgets.interactive_output(f, {"prop": prop})

def get_yield_variable(f):
    variables = [ key for key in f.variables.keys() if key.startswith("yield_") ]
    return next(iter(variables), None)

def get_colormap(data=None):
    """get a branca.colormap object adapted to the data

    :data: list of data
    :returns: a colormap

    """
    colors = ['white', 'green', 'yellow', 'orange', 'darkred']
    if data is None:
        return cm.LinearColormap(colors=colors)
    mn = min(data)
    mx = max(data)
    data_nozero = [ d for d in data if d > 0 ]
    qt = quantiles(data_nozero)
    return cm.LinearColormap(colors=colors, index=[mn, *qt, mx], vmin=round(mn, 2), vmax=round(mx, 2))

year_regex = re.compile(r"(?P<base>.*)_(?P<start>[0-9]{4})_(?P<end>[0-9]{4})\.(?P<ext>\w{1,3})")
def get_start_year(path):
    return int(year_regex.match(path).group("start"))
def get_end_year(path):
    return int(year_regex.match(path).group("end"))
def get_base_from_year_path(path):
    return year_regex.match(path).group("base")
def get_ext_from_year_path(path):
    return year_regex.match(path).group("ext")

def is_contiguous(ranges):
    """check whether the year ranges are contiguous

    :ranges: sequence of tuples, containing integers
    :returns: Boolean, indicating whether the values are contiguous

    Each start number must be 1 greater than the end number of the previous tuple
    e.g.    (1981, 1990), (1991, 2000) => True
            (1971, 1980), (1991, 2000) => False
            (1971, 1980), (1980, 2000) => False

    """
    for prev, nxt in zip(ranges[:-1], ranges[1:]):
        if prev[1] + 1 != nxt[0]:
            return False
    return True

def get_combine_cache_file(paths):
    """compute the filename used to store the combined cache of the given files
    example paths: [
    'data/raw/IMAGE_LEITAP/GFDL-ESM2M/hist/ssp2/co2/firr/maize/image_gfdl-esm2m_hist_ssp2_co2_firr_yield_mai_annual_1971_1980.nc4',
    'data/raw/IMAGE_LEITAP/GFDL-ESM2M/hist/ssp2/co2/firr/maize/image_gfdl-esm2m_hist_ssp2_co2_firr_yield_mai_annual_1981_1990.nc4',
    ]

    :files: a list of strings containing the file names
    :returns: None if not combinable

    """
    assert paths and len(paths) > 0, "paths must not be empty"
    ranges = sorted([ (get_start_year(p), get_end_year(p)) for p in paths ])
    if not is_contiguous(ranges):
        return None
    combined_range = ranges[0][0], ranges[-1][1]
    path = basename(paths[0])
    base = get_base_from_year_path(path)
    ext = get_ext_from_year_path(path)

    combined_path = f"{base}_{combined_range[0]}_{combined_range[1]}.{ext}"
    return combined_path

def can_combine(paths):
    return get_combine_cache_file(paths) is not None


# https://stackoverflow.com/questions/61708701/how-to-download-a-file-using-ipywidget-button
class DownloadButton(widgets.Button):
    """Download button with dynamic content

    The content is generated using a callback when the button is clicked.
    """

    def __init__(self, filename: str, contents: Callable[[], bytes], **kwargs):
        super(DownloadButton, self).__init__(**kwargs)
        self.filename = filename
        self.contents = contents
        self.on_click(self.__on_click)

    def __on_click(self, b):
        contents: bytes = self.contents() # .encode('utf-8')
        b64 = base64.b64encode(contents)
        payload = b64.decode()
        digest = hashlib.md5(contents).hexdigest()  # bypass browser cache
        id = f'dl_{digest}'

        display(HTML(f"""
<html>
<body>
<a id="{id}" download="{self.filename}" href="data:text/csv;base64,{payload}" download>
</a>

<script>
(function download() {{
document.getElementById('{id}').click();
}})()
</script>

</body>
</html>
"""))

