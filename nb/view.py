# view.py - User interface for app
# rcampbel@purdue.edu - 2020-07-14

import ipywidgets as widgets
from ipyleaflet import Map, Marker, Popup, WidgetControl, Choropleth
from IPython.display import HTML, display, clear_output, FileLink
import logging
from branca.colormap import linear
from typing import Callable
import json
import csv
import base64
import hashlib

coordinates = [0, 0]

# https://stackoverflow.com/questions/61708701/how-to-download-a-file-using-ipywidget-button
class DownloadButton(widgets.Button):
    """Download button with dynamic content

    The content is generated using a callback when the button is clicked.
    """

    def __init__(self, filename: str, contents: Callable[[], str], **kwargs):
        super(DownloadButton, self).__init__(**kwargs)
        self.filename = filename
        self.contents = contents
        self.on_click(self.__on_click)

    def __on_click(self, b):
        contents: bytes = self.contents().encode('utf-8')
        b64 = base64.b64encode(contents)
        payload = b64.decode()
        digest = hashlib.md5(contents).hexdigest()  # bypass browser cache
        id = f'dl_{digest}'

        display(HTML(f"""
<html>
<body>
<a id="{id}" download="{self.filename}" href="data:text/csv;base64,{payload}" download>
</a>

<script>
(function download() {{
document.getElementById('{id}').click();
}})()
</script>

</body>
</html>
"""))


class View:

    LO10 = widgets.Layout(width='10%')
    LO15 = widgets.Layout(width='15%')
    LO20 = widgets.Layout(width='20%')

    def __init__(self):
        # The view's "public" attributes are listed here, with type hints, for
        # quick reference
        self.aggregate_btn: widgets.Button

        # Filer ("Selection" tab) controls
        self.filter_txt_startyr: widgets.Text
        self.filter_txt_endyr: widgets.Text
        self.filter_btn_apply: widgets.Button
        self.filter_ddn_ndisp: widgets.Dropdown
        self.filter_output: widgets.Output
        self.filter_btn_refexp: widgets.Button
        self.filter_out_export: widgets.Output

        # Plot ("Visualize" tab) controls
        self.plot_ddn: widgets.Dropdown
        self.plot_output: widgets.Output

        # Settings controls
        self.theme: widgets.Dropdown
        self.context: widgets.Dropdown
        self.fscale: widgets.FloatSlider
        self.spines: widgets.Checkbox
        self.gridlines: widgets.Text
        self.ticks: widgets.Checkbox
        self.grid: widgets.Checkbox
        self.figsize1: widgets.FloatSlider
        self.figsize2: widgets.FloatSlider
        self.apply: widgets.Button

    def props(self, props, header="Props: "):
        """ Get an output widget that interactively display the properties stored in a dict """
        def f(**kwargs):
            print(header)
            for k, v in kwargs.items():
                print(f"{k}: {v}")
        return widgets.interactive_output(f, props)

    def start(self, log=False):
        """Build the user interface."""

        # Create module-level singletons
        global logger, log_handler, Const, model
        from nb.cfg import logger, log_handler, Const, model

        # Optionally show additional info in log
        # if log:
        #     log_handler.setLevel(logging.INFO)
        #     logger.setLevel(logging.INFO)

        # Create user interface

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
        # tab_content.append(self.settings_content())

        tabs.children = tuple(tab_content)  # Fill tabs with content

        # Show the app
        header = widgets.HBox([app_title, logo])
        header.layout.justify_content = 'space-between'  # Example of custom widget layout
        display(widgets.VBox([header, tabs]))
        logger.info('UI build completed')

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
        content.append(self.section("Log", [log_handler.log_output_widget]))
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

        # dropdown
        self.dropdown = widgets.Dropdown(options=[],
                                         description='Select file',
                                         )

        content = [radio_layout,
                   self.props({'path': model.data_file_path}, "Props"),
                   self.dropdown]

        return self.section(Const.PREVIEW_SECTION_TITLE, content)

    def aggregation_content(self):
        '''Create widgets for selection tab content'''
        self.filter_txt_startyr = widgets.Text(
            description=Const.START_YEAR, value='', placeholder='')
        self.filter_txt_endyr = widgets.Text(
            description=Const.END_YEAR, value='', placeholder='')
        self.filter_btn_apply = widgets.Button(
            description=Const.CRITERIA_APPLY, icon='filter', layout=self.LO20)
        self.filter_ddn_ndisp = widgets.Dropdown(
            options=['25', '50', '100', Const.ALL], layout=self.LO10)
        self.filter_output = widgets.Output()
        self.filter_btn_refexp = widgets.Button(
            description=Const.EXPORT_BUTTON, icon='download', layout=self.LO20)
        self.filter_out_export = widgets.Output(
            layout={'border': '1px solid black'})

        self.aggregate_btn = widgets.Button(description="Aggregate")
        self.download_btn = DownloadButton(filename='out.csv', contents=lambda: 'hello', description='Download')

        # interactive display
        radio_selection_display = self.props(
            model.radio_selections, "Selections")

        self.range_slider = widgets.IntRangeSlider(
            value=[1990, 2010],
            min=1980,
            max=2020,
            step=1,
            description='Year Range',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
        )

        content = []
        content.append(
            self.section(
                "Data Aggregation", [
                    self.range_slider, self.aggregate_btn, self.download_btn, radio_selection_display]))

        return widgets.VBox(content)

    def visualize_content(self):
        '''Create widgets for visualize tab content'''
        content = []

        center = (0, 0)

# read prod data
        with open('data/countries.geo.json', 'r') as f:
            geodata = json.load(f)

        country_keys = [d['id'] for d in geodata['features']]
        countries = dict.fromkeys(country_keys, 0.0)


# create map
        content = []

        m = Map(center=center, zoom=2, close_popup_on_click=True)
        self.map = m

        def cb_map(**kwargs):
            if (kwargs['type'] == 'preclick'):
                global coordinates
                coordinates = kwargs['coordinates']
                # popup.close_popup()
                # print(coordinates)

        m.on_interaction(cb_map)

# prod_data = {1980: { 'AFG': 0, 'AGO': 135, ...}}
        prod_data = {}
        with open('data/out.csv', 'r') as f:
            for row in csv.DictReader(f):
                year = int(row['time'])
                country = row['id']
                production = float(row['production'])
                prod_data.setdefault(year, countries.copy())
                if country in prod_data[year]:
                    prod_data[year][country] = production
                else:
                    logger.warning(f"{country} not in dict")

        choro_data = prod_data[1980]
        choro = Choropleth(
            data=geodata.copy(),
            hover_style={
                'color': 'white', 'dashArray': '0', 'fillOpacity': 0.5
            },
            geo_data=geodata.copy(),
            choro_data=choro_data,
            colormap=linear.YlOrRd_04,
            border_color='black',
            style={'fillOpacity': 0.8, 'dashArray': '5, 5'})


# todo: use widget control, parameterize year range
# create slider
        zoom_slider = widgets.IntSlider(
            description='Year', min=1990, max=2020, value=1990)
        render_button = widgets.Button(description="Render")

        content.append(widgets.HBox([zoom_slider, render_button]))
        content.append(m)

# todo: use a computed prop to sync
        def on_value_change(change):
            # print(change)
            new_year = change['new']
            if new_year not in prod_data:
                logger.debug(f"Map: no data for year {new_year}")
            else:
                choro.choro_data = prod_data[new_year]
        zoom_slider.observe(on_value_change, names='value')

        def cb_geojson(**kwargs):
            # kwargs = {'event': 'click', 'feature': {'type': 'Feature',
            # 'properties': {'ADMIN': 'Ivory Coast', 'ISO_A3': 'CIV', 'style':
            # {'color': 'black', 'fillColor': 'red'}}, 'geometry': ..., ...}
            # print(coordinates)
            popup.open_popup(coordinates)
            feature_id = kwargs['feature']['id']
            popup.child = widgets.HTML(feature_id)

        choro.on_click(cb_geojson)

        m.add_layer(choro)

# create popup
        popup = Popup(
            location=center,
            close_button=True,
            auto_close=True,
            close_on_escape_key=True
        )
        m.add_layer(popup)
# todo: how to close popup on start?
# popup.close_popup()
        return self.section("Map", content)

    def settings_content(self):
        """Create widgets for settings tab."""
        self.theme = widgets.Dropdown(
            description=Const.THEME,
            options=Const.THEMES)
        self.context = widgets.Dropdown(
            description=Const.CONTEXT,
            options=Const.CONTEXTS)
        self.fscale = widgets.FloatSlider(
            description=Const.FONT_SCALE, value=1.4)
        self.spines = widgets.Checkbox(description=Const.SPINES, value=False)
        self.gridlines = widgets.Text(description=Const.GRIDLINES, value='--')
        self.ticks = widgets.Checkbox(description=Const.TICKS, value=True)
        self.grid = widgets.Checkbox(description=Const.GRID, value=False)
        self.figsize1 = widgets.FloatSlider(
            description=Const.FIG_WIDTH, value=6)
        self.figsize2 = widgets.FloatSlider(
            description=Const.FIG_HEIGHT, value=4.5)
        self.apply = widgets.Button(description=Const.APPLY)

        return(self.section(Const.PLOT_SETTINGS_SECTION_TITLE,
                            [self.theme, self.context, self.fscale, self.spines, self.gridlines,
                             self.ticks, self.grid, self.figsize1, self.figsize2, self.apply]))

    def set_no_data(self):
        """Indicate there are no results."""
        # NOTE While the other view methods build the UI, this one acts an
        # example of a helper method

        with self.filter_output:
            clear_output(wait=True)
            display(widgets.HTML(Const.NO_DATA_MSG))
