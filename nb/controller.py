# controller.py - Central logic for app
# rcampbel@purdue.edu - 2020-07-14

import traceback
from IPython.display import display, clear_output, FileLink
from jupyterthemes import jtplot
from matplotlib import pyplot as plt
import ipywidgets as widgets
from ipyleaflet import Choropleth, WidgetControl
import subprocess
from lib.python import SyncedProp
import numpy as np
import os
import re
from lib.python.utils import get_yield_variable, get_colormap, get_dir_content, \
    can_combine, get_combine_info, combine_nc4, get_summary_info, get_base_from_year_path
import netCDF4
import json
import csv

class Controller():

    def start(self):
        """Begin running the app."""

        # Create module-level singletons
        global model, view, logger, Const, send_notification
        from nb.cfg import model, view, logger, Const, send_notification

        try:
            ####################
            #  Data Selection  #
            ####################

            # model.radio_selections -> view.radios
            for radio in view.radios:
                model.radio_selections[radio.description] @ radio

            # model.data_file_path, model.radio_selections_info
            for category, prop in model.radio_selections.items():
                model.radio_selections_info << (prop, dict(name=category))
                model.data_file_path << prop # calculating data path doesn't need the name
            # TODO: refactor the method below into a lambda <2022-05-03, David Deng> #
            model.data_file_path >> model.get_data_file_path
            model.radio_selections_info >> (lambda **kwargs: kwargs) # output a dictionary

            model.folder_file_selection_options \
                << (model.data_file_path, dict(name="path")) \
                >> (lambda path: get_dir_content(path))

            SyncedProp() \
                << (model.folder_file_selection_options, dict(sync=True)) \
                >> (view.folder_file_multi_select, dict(prop='options', sync=True))

            model.select_all \
                << (view.select_all) \
                >> (view.folder_file_multi_select, dict(prop='disabled', sync=True))

            model.selected_files \
                << (model.data_file_path, dict(name="path")) \
                << (view.folder_file_multi_select, dict(prop="value", name="selected_files")) \
                << (view.folder_file_multi_select, dict(prop="options", name="all_files")) \
                << (model.select_all, dict(name="select_all")) \
                >> (lambda path, select_all, selected_files, all_files:
                    [ os.path.join(path, file) for file in (all_files if select_all else selected_files) ])

            model.selected_combinable \
                << (model.selected_files, dict(name='files')) \
                >> (lambda files: can_combine(files))

            SyncedProp() \
                << ~model.selected_combinable \
                >> (view.selection_next_btn, dict(prop='disabled', sync=True)) \
                >> (view.aggregate_btn, dict(prop='disabled', sync=True)) \
                >> (view.aggregation_options, dict(prop='disabled', sync=True)) \
                >> (view.aggregate_btn, dict(prop='disabled', sync=True)) \
                >> (view.region_map_select_upload, dict(prop='disabled', sync=True)) \

            # TODO: bind this to a variable indicating cache is generated <2022-05-04, David Deng> #
            SyncedProp() \
                << ~model.selected_combinable \
                >> (view.aggregation_next_btn, dict(prop='disabled', sync=True)) \
                >> (view.aggregated_download_btn, dict(prop='disabled', sync=True)) \
                >> (view.citation_btn, dict(prop='disabled', sync=True))

            model.selection_info \
                << (model.start_year, dict(name="start")) \
                << (model.end_year, dict(name="end")) \
                << (model.radio_selections_info, dict(name="model_info")) \
                >> (lambda start, end, model_info: {'Year Range': f"{start}-{end}", **model_info})

            model.raw_download_file_name \
                << (model.start_year, dict(name="start")) \
                << (model.end_year, dict(name="end")) \
                << (model.selected_files, dict(name="files")) \
                >> (lambda files, start, end: f"{get_base_from_year_path(os.path.basename(files[0]))}_{start}_{end}.zip"
                    if files else "unnamed.zip")

            SyncedProp() \
                << (model.raw_download_file_name, dict(sync=True)) \
                >> (view.raw_download_btn, dict(prop="filename", sync=True))

            ######################
            #  Data Aggregation  #
            ######################

            model.start_year \
                << (model.selected_files, dict(name="files")) \
                >> (lambda files: get_combine_info(files).get("start_year") if files else None)

            model.end_year \
                << (model.selected_files, dict(name="files")) \
                >> (lambda files: get_combine_info(files).get("end_year") if files else None)

            model.use_weightmap \
                << (view.aggregation_options, dict(name="op")) \
                >> (lambda op: op == "wa")

            model.aggregated_download_file_name \
                << (view.aggregation_options, dict(name="op")) \
                << (model.start_year, dict(name="start")) \
                << (model.end_year, dict(name="end")) \
                << (model.selected_files, dict(name="files")) \
                >> (lambda files, start, end, op: f"{get_base_from_year_path(os.path.basename(files[0]))}_{start}_{end}_{op}.csv"
                    if files else "unnamed.csv")

            SyncedProp() \
                << (model.aggregated_download_file_name, dict(sync=True)) \
                >> (view.aggregated_download_btn, dict(prop="filename", sync=True))


            view.aggregate_btn.on_click(self.cb_aggregate)

            ########################
            #  Data Visualization  #
            ########################

            model.selected_info \
                << (model.selected_country, dict(name="country")) \
                << (model.choro_data, dict(name="data")) \
                >> (lambda country, data: {
                    "Name": country,
                    "Production": round(data.get(country, 0), 2),
                })

            model.time_series_info \
                << (model.selected_country, dict(name="country")) \
                << (model.start_year, dict(name="start")) \
                << (model.end_year, dict(name="end")) \
                << (model.prod_data, dict(name="full_data")) \
                >> (lambda start, end, country, full_data: {
                    "x": np.arange(start, end+1, 1),
                    "y": np.array([ d[country] for d in full_data.values() ])
                })

            model.summary_info \
                << (model.choro_data, dict(name="choro")) \
                >> (lambda choro: get_summary_info(choro.values()))

            # add callback to map
            view.map.on_interaction(self.cb_set_coordinates)

            model.choro_data \
                << (view.zoom_slider, dict(name='selected_year', sync=False)) \
                << (model.prod_data, dict(name='prod_data', sync=False)) \
                >> (lambda prod_data, selected_year: prod_data.get(selected_year, None))

            SyncedProp() \
                << (model.selected_files, dict(sync=True, trans=lambda fs: not bool(fs))) \
                >> (view.raw_download_btn, dict(prop='disabled', sync=True))

            # TODO: Fix Choropleth so that can automatically trigger update upon changing choro_data without creating new instance?
            # This is also challenging because Choropleth's choro_data attribute is very picky. E.g. no empty value allowed, etc.
            # Current solution is to manually update the view.choro.choro_data attribute upon changing the slider.
            # # model.choro_data.value <-> view.choro.choro_data
            # SyncedProp() \
            #     .add_input_prop(model.choro_data) \
            #     .add_output_prop(view.choro, 'choro_data')

            # Register callbacks
            view.zoom_slider.observe(self.cb_refresh_map, names='value')

            logger.info('App running')

        except Exception:
            logger.debug('Exception while setting up callbacks...\n'+traceback.format_exc())
            raise

    def cb_refresh_map(self, change):
        self.refresh_map()

    def cb_popup(self, **kwargs):
        model.selected_country.value = kwargs['feature']['id']
        # TODO: fix popup <2022-03-19, David Deng> #
        # view.popup.open_popup(model.coordinates)
        # feature_id = kwargs['feature']['id']
        # view.popup.child = widgets.HTML(feature_id)

    def cb_set_coordinates(self, **kwargs):
        if (kwargs['type'] == 'preclick'):
            # record the coordinate clicked
            model.coordinates = kwargs['coordinates']

    def cb_aggregate(self, _):
        # input_file = "data/epic_hadgem2-es_hist_ssp2_co2_firr_yield_soy_annual_1980_2010.nc4"
        send_notification("Aggregating data...")
        # TODO: merge the files, retrieve from cache <2022-04-07, David Deng> #
        input_files = model.selected_files.value
        if not input_files:
            logger.error("Trying to aggregate without an input file selected")
            return
        info = get_combine_info(input_files)
        # TODO: output to cache dir, implement cache? <2022-04-13, David Deng> #
        combine_nc4(input_files, info['file_name'])
        input_file = info['file_name']

        aggregation_option = view.aggregation_options.value
        weightmap_file = view.weight_map_select_upload.value
        regionmap_file = view.region_map_select_upload.value
        start_year = model.start_year.value
        end_year = model.end_year.value
        if start_year is None:
            logger.error("Trying to aggregate with start year of None")
            return
        if end_year is None:
            logger.error("Trying to aggregate with end year of None")
            return

        # TODO: refactor this to a method, to be used in citation <2022-03-31, David Deng> #
        with netCDF4.Dataset(input_file) as f:
            yield_var = get_yield_variable(f)
        if yield_var is None:
            logger.error("Trying to aggregate with yield_var of None")
            return
        logger.info(f"yield_var: {yield_var}")
        crop_name = Const.FULL_CROP_NAME.get(yield_var.lstrip("yield_"), "others")
        logger.info(f"crop_name: {crop_name}")

        cmd = [
            "Rscript",
            f"{Const.R_SCRIPT_DIR}/agmip.run.r",
            f"{Const.R_SCRIPT_DIR}/agmip.fns.r",
            input_file,
            regionmap_file,
            aggregation_option,
            weightmap_file,
            str(start_year),
            str(end_year),
            yield_var,
            "out.csv", # use dedicated name when cache is implemented
            "lon",
            "lat",
            crop_name,
            Const.WEIGHT_MAP_DIR,
        ]
        result = subprocess.run(cmd, capture_output=True)
        logger.info(" ".join(cmd))
        if result.returncode == 0:
            logger.info(f"R script completed: {result.stdout.decode('utf-8')}")
            send_notification("Successfully aggregated data!")
            view.switch_to_tab(3)
            self.cb_draw_map(None)
        else:
            logger.error(f"R script failed with return code {result.returncode}: {result.stderr.decode('utf-8')}")

    def cb_draw_map(self, _):
        logger.info("Drawing map...")
        primary_variable = Const.PRIMARY_VAR.get(view.aggregation_options.value)

        logger.info("primary_variable: {}".format(primary_variable))

        # retrieve and process all data
        country_keys = [d['id'] for d in model.geodata['features']]
        countries = dict.fromkeys(country_keys, 0.0)

        # update prod_data
        prod_data = {}
        # prod_data = {1980: { 'AFG': 0, 'AGO': 135, ...}}
        with open('out.csv', 'r') as f:
            for row in csv.DictReader(f):
                year = int(row['time'])
                country = row['id']
                # TODO: handle NA values <2022-03-19, David Deng> #
                try:
                    value = float(row[primary_variable])
                except ValueError as e:
                    # logger.error(e)
                    value = 0
                prod_data.setdefault(year, countries.copy())
                if country in prod_data[year]:
                    prod_data[year][country] = value

        model.prod_data.value = prod_data

        # reset zoom slider
        # NOTE: first set to 0 to prevent min > max error <2022-03-04, David Deng> #
        view.zoom_slider.min = 0
        view.zoom_slider.max = model.end_year.value
        view.zoom_slider.min = model.start_year.value
        view.zoom_slider.value = model.start_year.value

        view.reset_map_choro(model.choro_data.value)
        view.choro.on_click(self.cb_popup)

        self.refresh_map()

        send_notification("Successfully drawn map!")

    def refresh_map(self):
        if model.choro_data.value is not None:
            view.refresh_map_choro(model.choro_data.value)

            # # uncomment the following lines to show more visible update upon refreshing map
            # import random
            # view.refresh_map_choro({ k:v*random.uniform(0.5,1.5) for k,v in model.choro_data.value.items() })

            view.refresh_map_colormap()
            logger.debug("Map refreshed.")
