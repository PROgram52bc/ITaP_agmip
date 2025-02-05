# model.py - Storage access for app
# rcampbel@purdue.edu - 2020-07-14

import os
import csv
import glob
import pandas as pd
from lib.python import SyncedProp, ComputedProp, Prop
import json

class Model:

    def __init__(self):
        # The models's "public" attributes are listed here, with type hints, for quick reference
        self.coordinates: list = [0,0]

    def start(self):
        """Read data and/or prepare to query data."""

        # Create module-level singletons
        global logger, Const
        from app.cfg import logger, Const

        ####################
        #  Data Selection  #
        ####################

        # a list of (category_name: str, prop: SyncedProp), indicating the crop selection for each category
        self.radio_selections = [ (category['label'], SyncedProp(value=None)) for category in Const.DATA_CATEGORIES ]
        # a dictionary of values
        self.radio_selections_info = ComputedProp()

        # the path to search for input files, based on the radio_selections
        self.data_file_path = ComputedProp()
        # the files available in data_file_path
        self.selected_file = ComputedProp()

        # whether to select all files in data_file_path
        self.select_all = SyncedProp(value=False)
        # the selected files
        self.selected_files = ComputedProp()

        # a dictionary summarizing the selection info
        # 'start_year': ..., None if not combinable
        # 'end_year': ..., None if not combinable
        # 'model': {...} based on radio selection
        # 'agmip_files': [..., ...]
        self.selection_info = ComputedProp()

        self.raw_download_file_name = ComputedProp()

        ######################
        #  Data Aggregation  #
        ######################

        # start and end year based on data selection
        # TODO: replace with selection_info? <2022-05-03, David Deng> #
        self.start_year = ComputedProp()
        self.end_year = ComputedProp()

        # true only when the Weighted-Average aggregation option is selected
        self.use_weightmap = ComputedProp()

        self.aggregation_info = ComputedProp()

        ########################
        #  Data Visualization  #
        ########################

        # TODO: move to Const <2022-05-03, David Deng> #
        with open('data/countries.geo.json', 'r') as f:
            self.geodata = json.load(f)

        self.prod_data = Prop(value=None) # production data
        self.choro_data = ComputedProp()

        # mapinfo related data
        self.selected_country = SyncedProp(value=None)
        self.selected_info = ComputedProp()
        self.summary_info = ComputedProp()

        self.time_series_info = ComputedProp()

        self.aggregated_download_file_name = ComputedProp()

        logger.info('Data load completed')

    def get_data_file_path(self):
        """ Get the data file path based on radio_selections """
        # Works because dict is ordered
        path_segments = [ p[1].value for p in self.radio_selections ]
        if None in path_segments:
            return None
        else:
            # acea_gfdl-esm4_historical_default_production_and_yield_grid.RData
            return "_".join(path_segments[:-1]) + "_default_production_and_yield_grid.RData"
