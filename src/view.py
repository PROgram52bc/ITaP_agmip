# view.py - User interface for app
# rcampbel@purdue.edu - 2020-07-14

import ipywidgets as widgets
from ipyleaflet import Map, Marker, Popup, WidgetControl, Choropleth
from IPython.display import HTML, display, clear_output, FileLink
import logging
from branca.colormap import linear
from lib.python.prop import displayable
from lib.python.utils import get_dir_content, DownloadButton, get_colormap, is_float, zipped, conditional_widget, get_citation, remap_dict_keys, labeled_widget, hbox_scattered
import matplotlib.pyplot as plt
import numpy as np
from lib.python.upload import SelectOrUpload


class View:

    def __init__(self):
        # The view's "public" attributes are listed here, with type hints, for
        # quick reference
        self.aggregate_btn: widgets.Button
        self.colormap: branca.colormap.LinearColormap

    def start(self, log=False):
        """Build the user interface."""

        # Create module-level singletons
        global logger, log_handler, Const, model, notification
        from src.cfg import logger, log_handler, Const, model, notification

        # Send app's custom styles (CSS code) down to the browser
        display(HTML(filename=Const.CSS_JS_HTML))

        # Create large title for app
        app_title = widgets.HTML(Const.APP_TITLE)
        # Example of custom widget style via CSS, see custom.html
        app_title.add_class('app_title')

        # Create app logo - example of using exposed layout properties
        with open(Const.LOGO_IMAGE, "rb") as logo_file:
            logo = widgets.Image(
                value=logo_file.read(), format='jpg', layout={
                    'max_height': '64px'})

        self.notification = notification

        # Create tabs and fill with UI content (widgets)

        tabs = widgets.Tab()
        self.tabs = tabs

        # Add title text for each tab
        for i, tab_title in enumerate(Const.TAB_TITLES):
            tabs.set_title(i, tab_title)

        # Build conent (widgets) for each tab
        tab_content = []
        tab_content.append(self.welcome_content())
        tab_content.append(self.data_content())
        tab_content.append(self.aggregation_content())
        tab_content.append(self.visualize_content())

        tabs.children = tuple(tab_content)  # Fill tabs with content

        log = self.section("Log", [log_handler.log_output_widget])


        # initialize placeholders
        self.colormap = get_colormap()

        # Show the app
        header = widgets.HBox([app_title, logo])
        header.layout.justify_content = 'space-between'  # Example of custom widget layout
        display(widgets.VBox([header, self.notification, tabs, log]))
        logger.info('UI build completed')

    def get_navigation_button(self, action="next", description=None):
        """get a navigation button for the tab

        :action: TODO
        :description: TODO
        :returns: TODO

        """
        if description is None:
            description = action

        btn = widgets.Button()
        if action == "next":
            btn.description = f"{description} ►"
            btn.on_click(lambda _: self.switch_to_tab(self.tabs.selected_index + 1))
        elif action == "prev":
            btn.description = f"◄ {description}"
            btn.on_click(lambda _: self.switch_to_tab(self.tabs.selected_index - 1))
        else:
            raise ValueError(f"Invalid action: {action}")

        return btn

    def switch_to_tab(self, idx):
        """switch to a given tab programmatically
        :index: the index of the tab

        """
        if idx < 0 or idx >= len(Const.TAB_TITLES):
            logger.error(f"Invalid tab index {idx}")
            return
        logger.debug(f"Switching to tab {idx}")
        self.tabs.selected_index = idx

    def section(self, title, contents, collapsed=False):
        '''Utility method that create a collapsible widget container'''

        if isinstance(contents, str):
            contents = [widgets.HTML(value=contents)]

        ret = widgets.Accordion(children=tuple([widgets.VBox(contents)]), selected_index=None if collapsed else 0)
        ret.set_title(0, title)
        return ret

    def welcome_content(self):
        '''Create widgets for introductory tab content'''
        # TODO: refactor USING_TEXT with displayable <2022-05-04, David Deng> #
        return self.section('Using This App', [
            widgets.HTML(Const.USING_TEXT),
            self.get_navigation_button("next", "Get Started")
        ])

    def data_content(self):
        '''Show data tab content'''
        self.radios = [widgets.RadioButtons(
            options=category['options'],
            # TODO: move style to custom.html <2022-04-07, David Deng> #
            style={'description_width': 'auto'},
            layout={'overflow': 'hidden', 'height': 'auto', 'width': 'auto'},
            description=category['label']
        ) for category in Const.DATA_CATEGORIES]

        # Hard-coded layout
        self.radio_layout = widgets.GridspecLayout(5, 4)
        self.radio_layout[:3, 0] = self.radios[0]
        self.radio_layout[:3, 1] = self.radios[1]
        self.radio_layout[:3, 2] = self.radios[2]
        self.radio_layout[3:, 0] = self.radios[3]
        self.radio_layout[3:, 1] = self.radios[4]
        self.radio_layout[3:, 2] = self.radios[5]
        self.radio_layout[:, 3] = self.radios[6]

        # download button
        self.raw_download_btn = DownloadButton(
            filename="unnamed.zip",
            contents=lambda: zipped(model.selected_files.value),
            description='Download')

        # multiselect
        self.folder_file_multi_select = widgets.SelectMultiple(options=[], description='Select files')
        self.select_all = widgets.Checkbox(
            value=True,
            description='Select All Available Files',
            disabled=False,
        )

        self.selection_previous_btn = self.get_navigation_button("prev", "Previous")
        self.selection_next_btn = self.get_navigation_button("next", "Next")

        content = [
            # self.section(
            #     "Info", [
            #         labeled_widget(conditional_widget(model.selected_files,
            #                                           displayable(model.selected_files),
            #                                           widgets.HTML("⚠️ Nothing selected")
            #                                           ), "Selected files"),
            #     ]),
            self.section(
                "Data Selection", [
                    labeled_widget(self.radio_layout, "Select Category"),
                    labeled_widget(
                    widgets.VBox([
                        self.select_all,
                        self.folder_file_multi_select,
                    ]), "Select Files"
                    ),
                    conditional_widget(
                        ~model.selected_combinable & model.selected_files,
                        widgets.HTML("⚠️ Please select files with contiguous years in order to proceed.")),
                    hbox_scattered(
                        self.selection_previous_btn,
                        self.raw_download_btn,
                        self.selection_next_btn,
                    )]),
        ]

        return widgets.VBox(content)

    def aggregation_content(self):
        '''Create widgets for selection tab content'''

        self.aggregate_btn = widgets.Button(description="Aggregate and Render Map")

        # static dropdown
        weightmaps = get_dir_content(Const.WEIGHT_MAP_DIR)

        # TODO: move the layout attributes to custom.html <2022-03-31, David Deng> #
        self.aggregation_options = widgets.RadioButtons(description="Aggregation Options",
            style={'description_width': 'auto'},
            layout={'overflow': 'hidden', 'height': 'auto', 'width': 'auto'},
            options=Const.AGGREGATION_OPTIONS)

        self.region_map_select_upload = SelectOrUpload(select_dir=Const.REGION_MAP_DIR,
                                                       upload_dir=Const.REGION_MAP_UPLOAD_DIR,
                                                       overwrite=True)

        self.weight_map_select_upload = SelectOrUpload(select_dir=Const.WEIGHT_MAP_DIR,
                                                       upload_dir=Const.WEIGHT_MAP_UPLOAD_DIR,
                                                       overwrite=True)

        self.citation_btn = DownloadButton(description="Documentation", filename="citations.txt", contents=lambda: (get_citation(
            { 'start_year': model.start_year.value,
             'end_year': model.end_year.value,
             **remap_dict_keys(model.radio_selections_info.value, Const.LABEL_TO_KEY) },
            { 'option': self.aggregation_options.value }
        )+Const.REFERENCES).encode('utf-8'))

        self.aggregation_previous_btn = self.get_navigation_button("prev", "Previous")
        self.aggregation_next_btn = self.get_navigation_button("next", "Next")
        # TODO: disable the button based on whether there is cache, read file from cache <2022-05-17, David Deng> #
        self.aggregated_download_btn = DownloadButton(
            filename="unnamed.csv",
            contents=lambda: open("out.csv", "rb").read(),
            description='Download')

        content = [
            self.section(
                "Info", [
                    labeled_widget(conditional_widget(model.selected_files,
                                                      displayable(model.selected_files),
                                                      widgets.HTML("⚠️ Nothing selected")
                                                      ), "Selected files"),
                    conditional_widget(
                        model.selected_combinable,
                        widgets.VBox([
                            labeled_widget(displayable(model.selection_info), "Data Selection Info"),
                        ]),
                        widgets.HTML("⚠️ Please select some files with contiguous years in order to aggregate.")),
                ], collapsed=True),
            self.section(
                "Data Aggregation", [
                    labeled_widget(self.region_map_select_upload, "Select Region Map"),
                    labeled_widget(
                        widgets.VBox([
                            self.aggregation_options,
                            conditional_widget(
                                model.use_weightmap & model.selected_combinable,
                                labeled_widget(self.weight_map_select_upload, "Select Weight Map", 4))
                        ]),
                        "Choose Aggregation Options"),
                    hbox_scattered(
                        self.aggregation_previous_btn,
                        self.aggregate_btn,
                        self.aggregated_download_btn,
                        self.citation_btn,
                        self.aggregation_next_btn,
                    ),
                ]),
        ]

        return widgets.VBox(content)


    def visualize_content(self):
        '''Create widgets for visualize tab content'''
        center = (0, 0)

# create map
        self.map = Map(center=center, zoom=2)

        # placeholder
        self.choro = Choropleth()
        self.map.add_layer(self.choro)
        # placeholder
        self.cmcontrol = WidgetControl(widget=widgets.Output())
        self.map.add_control(self.cmcontrol)

        self.zoom_slider = widgets.IntSlider(description='Year')
        zscontrol = WidgetControl(widget=self.zoom_slider, position="bottomleft", transparent_bg=True)
        self.map.add_control(zscontrol)

        # time series graph
        def plot(info):
            if info is None:
                return
            x, y = info['x'], info['y']
            fig, ax = plt.subplots(constrained_layout=True, figsize=(6, 4))
            ax.grid(True)
            line, = ax.plot(x, y)
            plt.show()

        self.time_series = widgets.interactive_output(plot, {'info': model.time_series_info})

        content = [
            self.section("Info", [
                hbox_scattered(
                    labeled_widget(displayable(model.radio_selections_info), "Crop Model Selection"),
                    widgets.VBox([
                        labeled_widget(displayable(model.selected_info), "Selected Country Info"),
                        labeled_widget(self.time_series, "Time Series Trend"),
                    ]),
                    labeled_widget(displayable(model.summary_info), "Summary Statistics"),
                )
            ], collapsed=True),
            self.section("Map", [
                self.map,
                self.get_navigation_button("prev", "Previous"),
            ]),
        ]
        return widgets.VBox(content)

    def refresh_map_colormap(self):
        # replace the colormap legend control
        self.map.remove_control(self.cmcontrol)
        cm = widgets.Output()
        cm.append_display_data(self.colormap)
        self.cmcontrol = WidgetControl(widget=cm, position="topright", transparent_bg=True)
        self.map.add_control(self.cmcontrol)

    def refresh_map_choro(self, choro_data):
        data = list(choro_data.values())
        self.colormap = get_colormap(data)

        with self.choro.hold_trait_notifications():
            self.choro.colormap = self.colormap
            self.choro.choro_data = choro_data.copy()

    def reset_map_choro(self, choro_data):
        # similar to refresh_map_choro, except will recreate a new Choropleth object
        # used on initial rendering of the map.

        data = list(choro_data.values())
        self.colormap = get_colormap(data)

        # first remove the old layer.
        self.map.remove_layer(self.choro)

        # create a new choropleth layer
        self.choro = Choropleth(
            geo_data=model.geodata,
            choro_data=choro_data,
            colormap=self.colormap,
            hover_style={'color': 'white', 'dashArray': '0', 'fillOpacity': 0.5},
            style={'fillOpacity': 0.8, 'dashArray': '5, 5'},
            border_color='black',
        )
        self.map.add_layer(self.choro)

