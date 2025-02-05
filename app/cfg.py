# cfg.py - Constants and singletons for notebook
# rcampbel@purdue.edu - 2022-01-05

import logging
import ipywidgets as widgets
import threading

from app.model import Model
from app.view import View
from app.controller import Controller

class Const:
    """Store app-wide constants, including values and language text."""

    # General
    APP_TITLE = "AgMIP Tool: A GEOSHARE tool for aggregating outputs from the AgMIP's Global Grid (Phase 3)"
    CSS_JS_HTML = 'app/custom.html'
    LOGO_IMAGE = 'assets/agmip2.jpg'
    TAB_TITLES = [
        'Welcome',
        'Data Selection',
        'Data Aggregation',
        'Data Visualization']

    # Welcome tab
    MANUAL_PATH = 'assets/user_manual.pdf'
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

    DATA_CATEGORIES = [
        {"label": "Global Gridded Crop Models (GGCM)", "options": [
            ("AquaCropEarth@lternatives (ACEA)", "acea"),
            ("CROVER",                           "crover"),
            ("CYGMA (1p74)",                     "cygma1p74"),
            ("DSSAT-Pythia",                     "dssat-pythia"),
            ("EPIC-IIASA",                       "epic-iiasa"),
            ("ISAM",                             "isam"),
            ("LandscapeDNDC",                    "ldndc"),
            ("LPJmL",                            "lpjml"),
            ("pDSSAT",                           "pdssat"),
            ("PEPIC",                            "pepic"),
            ("PROMET",                           "promet"),
            ("SIMPLACE-LINTUL5+",                "simplace-lintul5"),
        ]},
        {"label": "Global Circulation Models (GCM)", "options": [
            ("GFDL-ESM4",     "gfdl-esm4"),
            ("GSWP3-W5E5",    "gswp3-w5e5"),
            ("IPSL-CM6A-LR",  "ipsl-cm6a-lr"),
            ("MPI-ESM1-2-HR", "mpi-esm1-2-hr"),
            ("MRI-ESM2-0",    "mri-esm2-0"),
            ("UKESM1-0-LL",   "ukesm1-0-ll"),
            ("WFDE5",         "wfde5"),
        ]},
        {"label": "Representative Concentration Pathways (RCP)", "options": [
            ("RCP2.6 (SSP126)",  "ssp126"),
            ("RCP8.5 (SSP585)",  "ssp585"),
            ("Historical",       "historical"),
            ("Observed Climate", "obsclim"),
        ]},
        {"label": "Crops", "options": [
            ("Maize",        "maize"),
            ("Spring Wheat", "spring_wheat"),
            ("Winter Wheat", "winter_wheat"),
            ("Soybean",      "soybeans"),
            ("Rice",         "rice"),
        ]}
    ]

    # TODO: refactor those maps <2022-05-03, David Deng> #

    LABEL_TO_KEY = {
        "Crop Model": "model",
        "GCM": "gcm",
        "RCP": "rcp",
        "SSP": "ssp",
        "CO2": "co2",
        "IRR": "irr",
        "Crop": "crop",
    }

    FULL_CROP_NAME = {
        "bar": "barley",
        "mai": "maize",
        "mgr": "managed_grass",
        "mil": "millet",
        "rap": "rapeseed",
        "ric": "rice",
        "sor": "sorghum",
        "soy": "soybean",
        "sgb": "sugarbeet",
        "sug": "sugarcane",
        "tea": "tea",
        "whe": "wheat",
    }

    # Selection tab
    RAW_DATA_DIR = '/data/tools/agmip/rdata/'
    COMBINED_CACHE_DIR = 'cache/combined/'
    AGGREGATED_CACHE_DIR = 'cache/aggregated/'
    WEIGHT_MAP_DIR = 'data/weightmap/'
    WEIGHT_MAP_UPLOAD_DIR = 'cache/weightmaps/'
    R_SCRIPT_DIR = 'lib/rfunctions/'

    REGION_MAP_DIR = 'data/regionmap/'
    REGION_MAP_UPLOAD_DIR = 'cache/regionmaps/'

    AGGREGATION_OPTIONS = [
        # ("Regional Production (in metric tons)", 'pr'),
        # ("Regional Yields (metric tons / hectare) Weighted by each Gridcells Havested Area", 'yi'),
        ("Summary Statistics (mean, median, SD, min, max, and 25%-75% percentiles)", 'st'),
        ("Regional Weighted-Average Yields (metric tons / hectare)", 'wa')
    ]

    PRIMARY_VAR = {
        'pr': 'production',
        'yi': 'harea.w.yield',
        'st': 'mean',
        'wa': 'w.ave.yield',
    }

    REFERENCES = """References


Elliott, J., C. Mueller, D. Deryng, J. Chryssanthacopoulos, K. J. Boote, M. Buechner, I. Foster, et al. 2014. "The Global Gridded Crop Model Intercomparison: Data and Modeling Protocols for Phase 1 (v1.0)." Geosci. Model Dev. Discuss. 7 (4): 4383-4427.


Rosenzweig, C., J. Elliott, D. Deryng, A.C. Ruane, C. Mueller, A. Arneth, K.J. Boote, C. Folberth, M. Glotter, N. Khabarov, K. Neumann, F. Piontek, T.A.M. Pugh, E. Schmid, E. Stehfest, H. Yang, and J.W. Jones. 2014. "Assessing agricultural risks of climate change in the 21st century in a global gridded crop model intercomparison." Proceedings of the National Academy of Sciences 111:3268-3273.


Villoria N.B, J. Elliot , C. Mueller, J. Shin, L. Zhao. C. Song. (2015). Rapid aggregation of globally gridded crop model outputs to facilitate cross-disciplinary analysis of climate change impacts in agriculture. Data tool accessible at url: https://mygeohub.org/resources/agmip


For definitions, descriptions, and limitations of these data please refer to Rosenzweig et al (2014) PNAS 111(9): 3268-3273.
http://www.pnas.org/content/111/9/3268.full


Different applications of these data can be found at:

Rosenzweig, C. et al. (2014). Assessing agricultural risks of climate change in the 21st century in a global gridded crop model intercomparison. Proceedings of the National Academy of Sciences, 111 (9): 3268-3273.

Elliott, J. et al. (2014). Constraints and potentials of future irrigation water availability on global agricultural production under climate change. Proceedings of the National Academy of Sciences, 111 (9): 3239-3244.

Mueller, Christoph, and Richard D. Robertson. "Projecting future crop productivity for global economic modeling." Agricultural Economics 45.1 (2014): 37-50.

Nelson, J. et al. (2014). Climate change effects on agriculture: Economic responses to biophysical shocks. Proceedings of the National Academy of Sciences, 111 (9):  3274-3279.


Links to the models used in the Phase I of the Global Gridded Crop Model Intercomparison (GGCMI) project:
Crop Models
EPIC         http://epicapex.tamu.edu/epic/
GEPIC        http://www.envirogrids.net/Materials/GEPIC/Workshop/1-Introduction/index.html
pDSSAT       https://rdcep.org/research/pdssat-productivity-and-climate-impact-models-0
LPJmL        https://www.pik-potsdam.de/research/projects/activities/biosphere-water-modelling/lpjml
IMAGE-LEITAP http://www.pbl.nl/en/publications/2006/Integratedmodellingofglobalenvironmentalchange.AnoverviewofIMAGE2.4
PEGASUS      http://onlinelibrary.wiley.com/doi/10.1029/2009GB003765/abstract
LPJ-GUESS    http://iis4.nateko.lu.se/lpj-guess/

GCMs
HadGEM2-ES     https://verc.enes.org/models/earthsystem-models/metoffice-hadley-centre/hadgem2-es
IPSL-CM5A-LR   https://verc.enes.org/models/earthsystem-models/ipsl/ipslesm
MIROC-ESM-CHEM http://www.geosci-model-dev.net/4/845/2011/gmd-4-845-2011.pdf
GFDL-ESM2M     http://www.gfdl.noaa.gov/earth-system-model
NorESM1-M      http://www.geosci-model-dev.net/6/687/2013/gmd-6-687-2013.html
"""

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
