# view.py - User interface for app
# rcampbel@purdue.edu - 2020-07-14

import ipywidgets as widgets
from ipyleaflet import Map, Marker, Popup, WidgetControl, Choropleth
from IPython.display import HTML, display, clear_output, FileLink
import logging
from branca.colormap import linear
from nb.utils import get_dir_content, displayable, DownloadButton, get_colormap, is_float, get_file_content, display_with_style, zipped


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

    def section(self, title, contents):
        '''Utility method that create a collapsible widget container'''

        if isinstance(contents, str):
            contents = [widgets.HTML(value=contents)]

        ret = widgets.Accordion(children=tuple([widgets.VBox(contents)]))
        ret.set_title(0, title)
        return ret

    def button_group(self, *buttons):
        """Create a horizontal list of buttons

        :*buttons: the list of buttons
        :returns: TODO

        """
        btns = widgets.HBox(children=buttons)
        btns.add_class("button_group")
        return btns

    def welcome_content(self):
        '''Create widgets for introductory tab content'''
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
        radio_layout = widgets.GridspecLayout(5, 4)
        radio_layout[:3, 0] = self.radios[0]
        radio_layout[:3, 1] = self.radios[1]
        radio_layout[:3, 2] = self.radios[2]
        radio_layout[3:, 0] = self.radios[3]
        radio_layout[3:, 1] = self.radios[4]
        radio_layout[3:, 2] = self.radios[5]
        radio_layout[:, 3] = self.radios[6]

        # download button
        self.raw_download_btn = DownloadButton(
            # TODO: name the zip file <2022-04-12, David Deng> #
            filename="unnamed.zip",
            contents=lambda: zipped(model.selected_files.value),
            description='Download')

        # multiselect
        self.folder_file_multi_select = widgets.SelectMultiple(options=[], description='Select file')
        self.select_all = widgets.Checkbox(
            value=True,
            description='Select All Available Files',
            disabled=False,
        )

        self.selection_previous_btn = self.get_navigation_button("prev", "Previous")
        self.selection_next_btn = self.get_navigation_button("next", "Next")

        content = [
            radio_layout,
            # displayable(model.data_file_path, "data file path"),
            self.select_all,
            self.folder_file_multi_select,
            displayable(model.selected_files, "Selected files"),
            self.button_group(
                self.selection_previous_btn,
                self.raw_download_btn,
                self.selection_next_btn,
            )
        ]

        return self.section("Data", content)

    def aggregation_content(self):
        '''Create widgets for selection tab content'''

        self.aggregate_btn = widgets.Button(description="Aggregate and Render Map")

        # TODO:
        # store the generated file and enable download in the map page
        # Separate aggregate and render?
        # self.aggregated_download_btn = DownloadButton(filename='aggregated.csv', contents=lambda: b'Empty', description='Download')

        # static dropdown
        weightmaps = get_dir_content(Const.WEIGHT_MAP_DIR)

        # TODO: move the layout attributes to custom.html <2022-03-31, David Deng> #
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
                    displayable(model.selected_files, "Agmip file"),
                    displayable(model.start_year, "Start year"),
                    displayable(model.end_year, "End year"),
                    self.aggregation_options,
                    self.weight_map_dropdown,
                    self.aggregate_btn,
                    # self.aggregated_download_btn,
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

        # TODO: fix popup <2022-03-29, David Deng> #
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
            if k == "Quantiles" and v is not None:
                display_with_style(round(v[0], 2), "1st Quantile")
                display_with_style(round(v[1], 2), "2nd Quantile")
                display_with_style(round(v[2], 2), "3rd Quantile")
            else:
                if is_float(v):
                    display_with_style(round(v, 2), k)
                else:
                    display_with_style(v, k)

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

