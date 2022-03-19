# view.py - User interface for app
# rcampbel@purdue.edu - 2020-07-14

import ipywidgets as widgets
from ipyleaflet import Map, Marker, Popup, WidgetControl, Choropleth
from IPython.display import HTML, display, clear_output, FileLink
import logging
from branca.colormap import linear
from nb.utils import get_dir_content, displayable, DownloadButton, get_colormap, is_float


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
        from nb.cfg import logger, log_handler, Const, model, notification

        # Send app's custom styles (CSS code) down to the browser
        display(HTML(filename=Const.CSS_JS_HTML))

        # Create large title for app
        app_title = widgets.HTML(Const.APP_TITLE)
        # Example of custom widget style via CSS, see custom.html
        app_title.add_class('app_title')

        # Create app logo - example of using exposed layout properties
        with open(Const.LOGO_IMAGE, "rb") as logo_file:
            logo = widgets.Image(
                value=logo_file.read(), format='png', layout={
                    'max_height': '32px'})

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

    def switch_to_tab(self, idx):
        """switch to a given tab programmatically
        :index: the index of the tab

        """
        if idx < 0 or idx >= len(Const.TAB_TITLES):
            logger.error(f"Invalid tab index {idx}")
            return
        logger.debug(f"Switching to tab {idx}")
        self.tabs.selected_index = idx

    def section(self, title, contents):
        '''Utility method that create a collapsible widget container'''

        if isinstance(contents, str):
            contents = [widgets.HTML(value=contents)]

        ret = widgets.Accordion(children=tuple([widgets.VBox(contents)]))
        ret.set_title(0, title)
        return ret

    def welcome_content(self):
        '''Create widgets for introductory tab content'''
        content = []
        content.append(self.section(Const.USING_TITLE, Const.USING_TEXT))
        return widgets.VBox(content)

    def data_content(self):
        '''Show data tab content'''
        self.radios = [widgets.RadioButtons(
            options=category['options'],
            style={'description_width': 'auto'},
            layout={'overflow': 'hidden', 'height': 'auto', 'width': 'auto'},
            description=category['label']
        ) for category in Const.DATA_CATEGORIES]

        # Hard-coded layout
        radio_layout = widgets.GridspecLayout(5, 4)
        radio_layout[:3, 0] = self.radios[0]
        radio_layout[:3, 1] = self.radios[1]
        radio_layout[:3, 2] = self.radios[2]
        radio_layout[3:, 0] = self.radios[3]
        radio_layout[3:, 1] = self.radios[4]
        radio_layout[3:, 2] = self.radios[5]
        radio_layout[:, 3] = self.radios[6]

        # download button
        # self.raw_download_btn = DownloadButton(filename=model.selected_file.value, contents=lambda: 'hello', description='Download')

        # dropdown
        self.folder_file_dropdown = widgets.Dropdown(options=[],
                                         description='Select file',
                                         )

        content = [
            radio_layout,
            displayable(model.data_file_path, "data file path"),
            displayable(model.selected_file, "selected file"),
            self.folder_file_dropdown,
            # self.raw_download_btn
                   ]

        return self.section(Const.PREVIEW_SECTION_TITLE, content)

    def aggregation_content(self):
        '''Create widgets for selection tab content'''

        self.aggregate_btn = widgets.Button(description="Aggregate and Render Map", layout={'width': 'auto'})

        # TODO: 
        # store the generated file and enable download in the map page
        # Separate aggregate and render?
        # self.aggregated_download_btn = DownloadButton(filename='aggregated.csv', contents=lambda: 'hello', description='Download')

        # static dropdown
        weightmaps = get_dir_content(Const.WEIGHT_MAP_DIR)

        self.aggregation_options = widgets.RadioButtons(description="Aggregation Options",
            style={'description_width': 'auto'},
            layout={'overflow': 'hidden', 'height': 'auto', 'width': 'auto'},
            options=Const.AGGREGATION_OPTIONS)

        self.weight_map_dropdown = widgets.Dropdown(description="Weightmap",
            options=weightmaps)

        self.worldids = widgets.Dropdown(description="")

        content = []
        content.append(
            self.section(
                "Data Aggregation", [
                    displayable(model.selected_file, "Agmip file"),
                    displayable(model.start_year, "Start year"),
                    displayable(model.end_year, "End year"),
                    self.aggregation_options,
                    self.weight_map_dropdown,
                    self.aggregate_btn,
                    # self.aggregated_download_btn
                ]))

        return widgets.VBox(content)


    def visualize_content(self):
        '''Create widgets for visualize tab content'''
        content = []
        center = (0, 0)


# create map
        content = []

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

        # don't add popup because can't close it
        # self.popup = Popup(location=(0,0), close_button=True, auto_close=True, close_on_escape_key=True)
        # self.map.add_layer(self.popup)

        self.mapinfo = widgets.interactive_output(self.render_mapinfo, {
            'Selected Country': model.selected_country,
            'Production': model.selected_value,
            'Minimum Value': model.choro_data_min,
            'Maximum Value': model.choro_data_max,
            'Standard Deviation': model.choro_data_stdev,
            'Quantiles': model.choro_data_quantiles,
        })

        content.append(self.map)
        content.append(self.mapinfo)
        return self.section("Map", content)

    def render_mapinfo(self, **kwargs):
        for k,v in kwargs.items():
            if k == "Quantiles":
                print(f"1st Quantile: {round(v[0], 2)}")
                print(f"2st Quantile: {round(v[1], 2)}")
                print(f"3st Quantile: {round(v[2], 2)}")
            else:
                # if is_float(v):
                #     print(f"{k}: {round(v, 2)}")
                # else:
                print(f"{k}: {v}")

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

