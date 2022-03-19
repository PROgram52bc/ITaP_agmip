# controller.py - Central logic for app
# rcampbel@purdue.edu - 2020-07-14

import traceback
from IPython.display import display, clear_output, FileLink
from jupyterthemes import jtplot
from matplotlib import pyplot as plt
import ipywidgets as widgets
from ipyleaflet import Choropleth, WidgetControl
import subprocess
from lib import SyncedProp
import os
from nb.utils import get_yield_variable, get_colormap
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
            view.aggregate_btn.on_click(self.cb_aggregate)

            # model.radio_selections -> view.radios
            for radio in view.radios:
                model.radio_selections[radio.description].sync_prop(radio)

            # model.radio_selections -> model.data_file_path
            model.data_file_path.add_inputs(*model.radio_selections.values())
            model.data_file_path.resync()

            # Connect to dropdown selection
            # model.dropdown_selections -> view.dropdown.options
            SyncedProp() \
                .add_input_prop(model.dropdown_selections, sync=True) \
                .add_output_prop(view.folder_file_dropdown, 'options', sync=True)

            # view.dropdown.value, model.data_file_path -> model.selected_file
            model.selected_file \
                .add_input(model.data_file_path, name="path") \
                .add_input(view.folder_file_dropdown, name="file") \
                .set_output(lambda path, file: os.path.join(path, file))

            # view.zoom_slider.value + model.prod_data.value -> model.choro_data.value
            model.choro_data \
                .add_input(view.zoom_slider, 'value', 'selected_year') \
                .add_input(model.prod_data, 'value', 'prod_data') \
                .set_output(lambda prod_data, selected_year: prod_data.get(selected_year, None))

            # add callback to map
            view.map.on_interaction(self.cb_set_coordinates)


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
        input_file = model.selected_file.value
        if input_file is None:
            logger.error("Trying to aggregate without an input file selected")
            return
        aggregation_option = view.aggregation_options.value
        weightmap_file = os.path.join(Const.WEIGHT_MAP_DIR, view.weight_map_dropdown.value)
        start_year = model.start_year.value
        end_year = model.end_year.value
        if start_year is None:
            logger.error("Trying to aggregate with start year of None")
            return
        if end_year is None:
            logger.error("Trying to aggregate with end year of None")
            return

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
            "examples/rfunctions/agmip.run.r",
            "examples/rfunctions/agmip.fns.r",
            input_file,
            "examples/regionmap/WorldId.csv",
            aggregation_option,
            weightmap_file,
            str(start_year),
            str(end_year),
            yield_var,
            "out.csv",
            "lon",
            "lat",
            crop_name,
            "examples/weightmap/"
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
        view.refresh_map_choro(model.choro_data.value)

        # # uncomment the following lines to show more visible update upon refreshing map
        # import random
        # view.refresh_map_choro({ k:v*random.uniform(0.5,1.5) for k,v in model.choro_data.value.items() })

        view.refresh_map_colormap()
        logger.debug("Map refreshed.")
