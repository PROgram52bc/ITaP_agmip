from os import listdir
from os.path import isfile, isdir, join
import ipywidgets as widgets
import branca.colormap as cm
from statistics import quantiles

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

# https://stackoverflow.com/questions/61708701/how-to-download-a-file-using-ipywidget-button
class DownloadButton(widgets.Button):
    """Download button with dynamic content

    The content is generated using a callback when the button is clicked.
    """
    import base64
    import hashlib
    from typing import Callable

    def __init__(self, filename: str, contents: Callable[[], str], **kwargs):
        super(DownloadButton, self).__init__(**kwargs)
        self.filename = filename
        self.contents = contents
        self.on_click(self.__on_click)

    def __on_click(self, b):
        contents: bytes = self.contents().encode('utf-8')
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

