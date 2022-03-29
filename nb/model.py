# model.py - Storage access for app
# rcampbel@purdue.edu - 2020-07-14

import os
import csv
import glob
import pandas as pd
from lib import SyncedProp, ComputedProp
from nb.utils import get_dir_content
import re
import json
from statistics import stdev, quantiles

class Model:

    def __init__(self):
        # The models's "public" attributes are listed here, with type hints, for quick reference
        self.data: pd.DataFrame
        self.results: pd.DataFrame
        self.res_count: int = 0
        self.headers: list
        self.ymin: int
        self.ymax: int
        self.coordinates: list = [0,0]

        pd.set_option('display.width', 1000)  # Prevent data desc line breaking

    def start(self):
        """Read data and/or prepare to query data."""

        # Create module-level singletons
        global logger, Const
        from nb.cfg import logger, Const

        # Load data into memory from file
        self.data = pd.read_csv(os.path.join(Const.DATA_DIR, Const.DATA_FILE), escapechar='#')
        self.headers = list(self.data.columns.values)

        with open('data/countries.geo.json', 'r') as f:
            self.geodata = json.load(f)

        self.radio_selections = { category['label']: SyncedProp(value=None) for category in Const.DATA_CATEGORIES }

        # radio_selections -> data_file_path
        self.data_file_path = ComputedProp()
        self.data_file_path.set_output(self.get_data_file_path)

        # data_file_path -> dropdown_selections
        self.dropdown_selections = ComputedProp() \
            .add_input(self.data_file_path, name="path") \
            .set_output(f=lambda path: get_dir_content(path))

        # data/raw/.../...nc4
        self.selected_file = ComputedProp()

        # TODO: use a transform property in SyncedProp <2022-03-19, David Deng> #

        self.no_selected_file = ComputedProp(use_none=True) \
            .add_input(self.selected_file, name='f') \
            .set_output(lambda f: not f) \
            .resync()

        year_regex = re.compile(Const.YEAR_REGEX)
        self.start_year = ComputedProp() \
            .add_input(self.selected_file, name='path') \
            .set_output(lambda path: int(year_regex.match(path).group(Const.YEAR_REGEX_START)))

        self.end_year = ComputedProp() \
            .add_input(self.selected_file, name='path') \
            .set_output(lambda path: int(year_regex.match(path).group(Const.YEAR_REGEX_END)))


        self.prod_data = SyncedProp(value=None) # production data

        # choropleth data based on the selected year
        self.choro_data = ComputedProp()

        # mapinfo related data
        self.selected_country = SyncedProp(value=None) #
        self.selected_value = ComputedProp() \
            .add_input(self.selected_country, name="country") \
            .add_input(self.choro_data, name="data") \
            .set_output(lambda country, data: data.get(country, 0))

        self.choro_data_max = ComputedProp() \
            .add_input(self.choro_data, name="choro") \
            .set_output(lambda choro: max(choro.values()))

        self.choro_data_min = ComputedProp() \
            .add_input(self.choro_data, name="choro") \
            .set_output(lambda choro: min(choro.values()))

        self.choro_data_stdev = ComputedProp() \
            .add_input(self.choro_data, name="choro") \
            .set_output(lambda choro: stdev(choro.values()))

        self.choro_data_quantiles = ComputedProp() \
            .add_input(self.choro_data, name="choro") \
            .set_output(lambda choro: quantiles(choro.values()))

        logger.info('Data load completed')


    def get_data_file_path(self):
        """ Get the data file path based on radio_selections """
        path_segments = [ p.value for p in self.radio_selections.values() ]
        if None in path_segments:
            return None
        else:
            return os.path.join("data/raw", *[p.value for p in self.radio_selections.values() if p.value is not None])
