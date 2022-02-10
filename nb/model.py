# model.py - Storage access for app
# rcampbel@purdue.edu - 2020-07-14

import os
import csv
import glob
import pandas as pd
from lib import SyncedProp, ComputedProp
from os import listdir
from os.path import isfile, isdir, join



class Model:

    def __init__(self):
        # The models's "public" attributes are listed here, with type hints, for quick reference
        self.data: pd.DataFrame
        self.results: pd.DataFrame
        self.res_count: int = 0
        self.headers: list
        self.ymin: int
        self.ymax: int

        pd.set_option('display.width', 1000)  # Prevent data desc line breaking

    def start(self):
        """Read data and/or prepare to query data."""

        # Create module-level singletons
        global logger, Const
        from nb.cfg import logger, Const

        # Load data into memory from file
        self.data = pd.read_csv(os.path.join(Const.DATA_DIR, Const.DATA_FILE), escapechar='#')
        self.headers = list(self.data.columns.values)

        self.radio_selections = { category['label']: SyncedProp(value="") for category in Const.DATA_CATEGORIES }
        self.data_file_path = ComputedProp()
        self.data_file_path.add_inputs(*self.radio_selections.values())
        self.data_file_path.set_output(self.get_data_file_path)
        self.dropdown_selections = ComputedProp((self.data_file_path, "value", "dir"),
                                                f=lambda **kwargs: self.get_dir_content(kwargs['dir']))

        # Get values for data selection  TODO ennforce data selection limits
        self.ymin = min(self.data[self.data.columns[0]])
        self.ymax = max(self.data[self.data.columns[0]])


        logger.info('Data load completed')

    def get_dir_content(self, dirpath):
        """ Get all files from a given directory.

        :dirpath: the path of the directory to be listed.
        :returns: a list of file names, empty if directory doesn't exist or there is no file in the directory.

        """
        return [f for f in listdir(dirpath) if isfile(join(dirpath, f))] if isdir(dirpath) else []

    def get_data_file_path(self):
        """ Get the data file path based on radio_selections """
        return os.path.join("data/raw", *[p.value for p in self.radio_selections.values() if p.value is not None])

    def set_disp(self, data=None, limit=None, wide=False):
        """Prep Pandas to display specific number of data lines."""
        if not limit:
            limit = data.shape[0]

        pd.set_option('display.max_rows', limit + 1)

        if wide:
            pd.set_option('display.float_format', lambda x: format(x, Const.FLOAT_FORMAT))

    def clear_filter_results(self):
        """Reset results-tracking attributes."""
        self.results = None
        self.res_count = 0

    def filter_data(self, from_year, to_year):
        '''Use provided values to filter data.'''
        self.results = self.data[(self.data[self.headers[0]] >= int(from_year)) &
                                 (self.data[self.headers[0]] <= int(to_year))]
        self.res_count = self.results.shape[0]
        logger.debug('Results: '+str(self.res_count))

    def iterate_data(self):
        """Get iterator for data."""
        return self.data.itertuples()

    def create_download_file(self, data, file_format_ext):
        """Prep data for export."""

        # First, to save space, delete existing download file(s)
        for filename in glob.glob(Const.DOWNLOAD_DATA_NAME + '.*'):
            os.remove(filename)

        # Create new download file TODO Other download formats
        filename = Const.DOWNLOAD_DATA_NAME + '.' + file_format_ext
        data.to_csv(filename, index=False, quoting=csv.QUOTE_NONNUMERIC)

        return filename
