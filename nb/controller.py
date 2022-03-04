# controller.py - Central logic for app
# rcampbel@purdue.edu - 2020-07-14

import traceback
from IPython.display import display, clear_output, FileLink
from jupyterthemes import jtplot
from matplotlib import pyplot as plt
import ipywidgets as widgets
import subprocess
from lib import SyncedProp
import os
from nb.utils import get_yield_variable
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
                .set_output(lambda prod_data, selected_year: prod_data.get(selected_year))

            # add callback to map
            view.map.on_interaction(self.cb_set_coordinates)
            view.choro.on_click(self.cb_popup)

            # model.choro_data.value <-> view.choro.choro_data
            SyncedProp() \
                .add_input_prop(model.choro_data) \
                .add_output_prop(view.choro, 'choro_data')

            logger.info('App running')

        except Exception:
            logger.debug('Exception while setting up callbacks...\n'+traceback.format_exc())
            raise

    def cb_popup(self, **kwargs):
        view.popup.open_popup(model.coordinates)
        feature_id = kwargs['feature']['id']
        view.popup.child = widgets.HTML(feature_id)

    def cb_set_coordinates(self, **kwargs):
        if (kwargs['type'] == 'preclick'):
            # record the coordinate clicked
            model.coordinates = kwargs['coordinates']

    def cb_aggregate(self, _):
        # input_file = "data/epic_hadgem2-es_hist_ssp2_co2_firr_yield_soy_annual_1980_2010.nc4"
        input_file = model.selected_file.value
        if input_file is None:
            send_notification("Trying to aggregate without an input file selected")
            return
        aggregation_option = view.aggregation_options.value
        start_year = model.start_year.value
        end_year = model.end_year.value
        if start_year is None:
            send_notification("Trying to aggregate with start year of None")
            return
        if end_year is None:
            send_notification("Trying to aggregate with end year of None")
            return

        with netCDF4.Dataset(input_file) as f:
            yield_var = get_yield_variable(f)
        if yield_var is None:
            send_notification("Trying to aggregate with yield_var of None")
            return

        cmd = [
            "Rscript",
            "examples/rfunctions/agmip.run.r",
            "examples/rfunctions/agmip.fns.r",
            input_file,
            "examples/regionmap/WorldId.csv",
            aggregation_option,
            "null",
            str(start_year),
            str(end_year),
            yield_var,
            "out.csv",
            "lon",
            "lat",
            "soybean", # TODO: let user select weightmap, change the Rscript interface.
            "examples/weightmap/"
        ]
        result = subprocess.run(cmd, capture_output=True)
        logger.info(" ".join(cmd))
        if result.returncode == 0:
            logger.info(f"R script completed: {result.stdout.decode('utf-8')}")
            send_notification("Successfully aggregated data!")
            self.cb_draw_map(None)
        else:
            logger.error(f"R script failed with return code {result.returncode}: {result.stderr.decode('utf-8')}")


    def cb_draw_map(self, _):
        logger.info("Drawing map...")
        primary_variable = Const.PRIMARY_VAR.get(view.aggregation_options.value)

        logger.info("primary_variable: {}".format(primary_variable))

        # retrieve and process all data
        with open('data/countries.geo.json', 'r') as f:
            geodata = json.load(f)
        country_keys = [d['id'] for d in geodata['features']]
        countries = dict.fromkeys(country_keys, 0.0)

        # update prod_data
        prod_data = {}
        # prod_data = {1980: { 'AFG': 0, 'AGO': 135, ...}}
        with open('out.csv', 'r') as f:
            for row in csv.DictReader(f):
                year = int(row['time'])
                country = row['id']
                value = float(row[primary_variable])
                prod_data.setdefault(year, countries.copy())
                if country in prod_data[year]:
                    prod_data[year][country] = value
                else:
                    logger.warning(f"{country} not in dict for year {year}")

        model.prod_data.value = prod_data

        # requires choro_data to be set before setting geodata
        view.choro.choro_data = prod_data[model.start_year.value]
        view.choro.data = geodata.copy()
        view.choro.geo_data = geodata.copy()
        # view.choro.choro_data = choro_data

        view.popup.close_popup() # close the popup

        # TODO: first set to 0 to prevent min > max error <2022-03-04, David Deng> #
        view.zoom_slider.max = model.end_year.value
        view.zoom_slider.min = model.start_year.value
        view.zoom_slider.value = model.start_year.value

        send_notification("Finished drawing map")

# todo: use a computed prop to sync
        # def on_value_change(change):
        #     # print(change)
        #     new_year = change['new']
        #     if new_year not in prod_data:
        #         logger.debug(f"Map: no data for year {new_year}")
        #     else:
        #         view.choro.choro_data = prod_data[new_year]
        # view.zoom_slider.observe(on_value_change, names='value')


    def cb_fill_results_export(self, _):
        """React to user pressing button to download results."""
        try:
            # Create link for filter results
            if model.res_count > 0:
                filename = model.create_download_file(model.results, 'csv')

                with view.filter_out_export:
                    clear_output(wait=True)
                    display(FileLink(filename, result_html_prefix=Const.EXPORT_LINK_PROMPT))

        except Exception:
            logger.debug('Exception during download creation...\n' + traceback.format_exc())
            raise

    def cb_apply_filter(self, _):
        """React to apply filter button press."""
        try:
            view.filter_out_export.clear_output()
            model.clear_filter_results()  # New search attempt so reset
            model.filter_data(view.filter_txt_startyr.value, view.filter_txt_endyr.value)
            self.refresh_filter_output()
        except Exception:
            logger.debug('Exception while filtering data...\n'+traceback.format_exc())

    def cb_ndisp_changed(self, _):
        """React to user changing result page size."""
        try:
            self.refresh_filter_output()
        except Exception:
            logger.debug('Exception while changing number of out lines to display...\n'+traceback.format_exc())

    def cb_plot_type_selected(self, _):
        """React to use requesting plot."""
        pass
        try:

            if not view.plot_ddn.value == Const.EMPTY:
                view.plot_output.clear_output(wait=True)
                # TODO Add ability to download plot as an image

                with view.plot_output:
                    plt.plot(model.results[model.headers[0]], model.results[view.plot_ddn.value])
                    plt.xlabel(model.headers[0])
                    plt.ylabel(view.plot_ddn.value)
                    plt.suptitle(Const.PLOT_TITLE)
                    plt.show()
                    logger.debug('Plot finished')
        except Exception:
            logger.debug('Exception while plotting...')
            raise
        finally:
            plt.close()

    def cb_apply_plot_settings(self, _):
        """React to user applying settings"""
        try:
            jtplot.style(theme=view.theme.value,
                         context=view.context.value,
                         fscale=view.fscale.value,
                         spines=view.spines.value,
                         gridlines=view.gridlines.value,
                         ticks=view.ticks.value,
                         grid=view.grid.value,
                         figsize=(view.figsize1.value, view.figsize2.value))
        except Exception:
            logger.debug('Exception while applying plot settings...')
            raise

    def refresh_filter_output(self):
        """Display filter results. Enable/disable plot widget(s)."""

        if model.res_count > 0:

            # Calc set output line limit
            if view.filter_ddn_ndisp.value == Const.ALL:
                limit = model.res_count
            else:
                limit = int(view.filter_ddn_ndisp.value)

            # Display results

            model.set_disp(limit=limit)

            with view.filter_output:
                clear_output(wait=True)
                display(model.results.head(limit))

            # Enable plot
            view.plot_ddn.disabled = False
            view.plot_ddn.options = [Const.EMPTY]+model.headers[1:]
        else:
            view.set_no_data()  # Show "empty list" msg
            view.plot_ddn.disabled = True
