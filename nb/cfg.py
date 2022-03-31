# cfg.py - Constants and singletons for notebook
# rcampbel@purdue.edu - 2022-01-05

import logging
import ipywidgets as widgets
import threading

from nb.model import Model
from nb.view import View
from nb.controller import Controller

class Const:
    """Store app-wide constants, including values and language text."""

    # NOTE This class is a simple catch-all. For better features, consider using the following:
    # - Multilingual internationalization: https://docs.python.org/2/library/gettext.html
    # - Data classes: https://docs.python.org/3/library/dataclasses.html
    # - Bound attributes: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch05s16.html

    # Data
    DATA_DIR = 'data'
    DATA_FILE = 'loti.csv'
    DOWNLOAD_DATA_NAME = 'loti-download'
    FLOAT_FORMAT = '0,.4f'

    # General
    APP_TITLE = 'Agmip Data Tool'
    CSS_JS_HTML = 'nb/custom.html'
    LOGO_IMAGE = 'examples/agmip2.jpg'
    ALL = 'All'
    EMPTY = ''
    NO_DATA_MSG = '''<br>(There's no data to display.)'''
    EXPORT_LINK_PROMPT = "Click here to save file: "
    TAB_TITLES = [
        'Welcome',
        'Data Selection',
        'Data Aggregation',
        'Data Visualization']
    PLOT_TITLE = 'Land-Ocean Temperature Index'

    # Welcome tab
    USING_TITLE = 'Using This App'
    MANUAL_PATH = 'examples/user_manual.pdf'
    USING_TEXT = f'''
    <h2>About This Tool</h2>
    <p>
    Crop Data Tool aggregates the yield shocks provided
    by the AgMIP project from their original 30x30 min resolution to the country level.
    <br>For detailed instructions, click this link.<br> <a href="{MANUAL_PATH}" download>
    AgMIP Tool 1.2 User Manual</a>
    </p>
    <h2>Usage</h2>
    <p>
    In the <b>Data Selection</b> tab above, you can select the dataset.
    </p>
    <p>
    In the <b>Data Aggregation</b> tab, you can select the aggregation option and aggregate the data.
    </p>
    <p>
    Once you've aggregated the data, generate plots in the <b>Data Visualization</b> tab.
    </p>'''
    SOURCES_TITLE = 'Data Sources'
    SOURCES_TEXT = '''<p>
    <b>Land-Ocean Temperature Index</b>
    <a href="https://climate.nasa.gov/vital-signs/global-temperature/"
    target="_blank">Global Temperature (NASA)</a>
    ,
    <a href="https://data.giss.nasa.gov/gistemp/"
    target="_blank">GISS Surface Temperature Analysis (NASA)</a>
    </p><p>
    This site is based on data downloaded from the following site on 2020-07-14:
    <a href="https://data.giss.nasa.gov/gistemp/graphs/graph_data/Global_Mean_Estimates_based_on_Land_and_Ocean_Data/graph.txt"  # noqa
    target="_blank">Global Mean Estimates based on Land_and Ocean Data (NASA)</a>
    </p>'''

    # Data tab
    PREVIEW_SECTION_TITLE = 'Data'
    DATA_CATEGORIES = [
        {"label": "Crop Model", "options": [
            "EPIC",
            "GEPIC",
            "IMAGE_LEITAP",
            "LPJ-GUESS",
            "LPJmL",
            "pDSSAT",
            "PEGASUS",
        ]},
        {"label": "GCM", "options": [
            "GFDL-ESM2M",
            "HadGEM2-ES",
            "IPSL-CM5A-LR",
            "MIROC-ESM-CHEM",
            "NorESM1-M",
        ]},
        {"label": "RCP", "options": [
            "hist",
            "rcp2p6",
            "rcp4p5",
            "rcp6p0",
            "rcp8p5",
        ]},
        {"label": "SSP", "options": [
            "ssp2",
        ]},
        {"label": "CO2", "options": [
            "co2",
            "noco2",
        ]},
        {"label": "IRR", "options": [
            "firr",
            "noirr",
        ]},
        {"label": "Crop", "options": [
            "maize",
            "managed_grass",
            "millet",
            "others",
            "rapeseed",
            "rice",
            "sorghum",
            "soy",
            "sugarcane",
            "tea",
            "wheat", ]}
    ]
    YEAR_REGEX = r".*(?P<start>[0-9]{4})_(?P<end>[0-9]{4})\.nc4"
    YEAR_REGEX_START = "start"
    YEAR_REGEX_END = "end"

    FULL_CROP_NAME = {
        "mai": "maize",
        "soy": "soybean",
        "whe": "wheat",
        "ric": "rice",
        "mgr": "managed_grass",
        "rap": "rapeseed",
        "bar": "barley",
        "mil": "millet",
        "sor": "sorghum",
        "sug": "sugarcane",
        "sgb": "sugarbeet",
        "tea": "tea",
    }

    # Selection tab
    START_YEAR = 'From Year'
    END_YEAR = 'To Year'
    WEIGHT_MAP_DIR = 'examples/weightmap/'
    AGGREGATION_OPTIONS = [
        ("Regional Production (in metric tons)", 'pr'),
        ("Regional Yields (metric tons / hectare) Weighted by each Gridcells Havested Area", 'yi'),
        ("Summary Statistics (mean, median, SD, min, max, and 25%-75% percentiles)", 'st'),
        ("Regional Weighted-Average Yields (metric tons / hectare)", 'wa')
    ]

    # Visualize tab
    PRIMARY_VAR = {
        'pr': 'production',
        'yi': 'harea.w.yield',
        'st': 'mean',
        'wa': 'w.ave.yield',
    }

    # Setting tab

class AppendFileLineToLog(logging.Filter):
    """Custom logging format"""
    def filter(_, record):
        record.filename_lineno = "%s:%d" % (record.filename, record.lineno)
        return True


class NotebookLoggingHandler(logging.Handler):
    """Format log entries and make them appear in Jupyter Lab's log output"""

    def __init__(self, log_level):
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter(
            '[%(levelname)s] %(message)s (%(filename_lineno)s)'))
        self.setLevel(log_level)
        self.log_output_widget = widgets.Output(layout={'overflow_y': 'auto', 'max_height': '500px'})

    def emit(self, record):
        """Write message to log"""
        message = self.format(record) + '\n'
        if record.levelno < logging.ERROR:
            self.log_output_widget.append_stdout(message)
        else:
            self.log_output_widget.append_stderr(message)


# Singletons

# TODO: reset the timer on new send_notification call
# see https://stackoverflow.com/questions/9812344/cancellable-threading-timer-in-python
# <2022-03-31, David Deng> #

notification = widgets.Output(layout={'display': 'none',
                                      'border': '1px solid black',
                                      'padding': '2px 0px 2px 0px'
                                      }) # hide by default

def send_notification(msg, hide_in=5):
    notification.layout.display = '' # display it
    notification.clear_output() # clear previous output
    with notification:
        print(msg)
    def hide_notification():
        notification.layout.display = 'none'
    threading.Timer(hide_in, hide_notification).start() # hide the notification later

logger = logging.getLogger(__name__)
log_handler = NotebookLoggingHandler(logging.INFO)
logger.addHandler(log_handler)
logger.addFilter(AppendFileLineToLog())
logger.setLevel(logging.DEBUG)
model = Model()
view = View()
ctrl = Controller()
