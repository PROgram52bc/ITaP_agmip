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

class Controller():

    def start(self):
        """Begin running the app."""

        # Create module-level singletons
        global model, view, logger, Const
        from nb.cfg import model, view, logger, Const

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
                .add_output_prop(view.dropdown, 'options', sync=True)

            # view.dropdown.value, model.data_file_path -> model.selected_file
            model.selected_file \
                .add_input(model.data_file_path, name="path") \
                .add_input(view.dropdown, name="file") \
                .set_output(lambda path, file: os.path.join(path, file) if path and file else "")

            logger.info('App running')

        except Exception:
            logger.debug('Exception while setting up callbacks...\n'+traceback.format_exc())
            raise

    def get_yield_variable(self, f):
        return [ key for key in f.variables.keys() if key.startswith("yield_") ]

    def cb_aggregate(self, _):
        input_file = "data/epic_hadgem2-es_hist_ssp2_co2_firr_yield_soy_annual_1980_2010.nc4"
        start_year = "1980"
        end_year = "2010"
        result = subprocess.run([
            "Rscript",
            "examples/rfunctions/agmip.run.r",
            "examples/rfunctions/agmip.fns.r",
            input_file,
            "examples/regionmap/WorldId.csv",
            "pr",
            "null",
            start_year,
            end_year,
            "yield_soy",
            "out.csv",
            "lon",
            "lat",
            "soybean", # TODO: let user select weightmap, change the Rscript interface.
            "examples/weightmap/"
        ])

        logger.info(str(result))

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
