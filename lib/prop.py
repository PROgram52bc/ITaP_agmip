from traitlets import HasTraits, TraitType, observe

class SyncedProp(HasTraits):
    """single synced prop to multiple widgets"""

    def __init__(self, *args):
        """ args is a list of 2-tuples (widget, prop) """
        self._widget_map = {}  # from id -> widget
        self._synced_props = set()
        self._listeners = []
        for (widget, prop) in args:
            self.sync_prop(widget, prop)

    def _observe_cb(self, change):
        # print("change received:")
        # print(change)
        self.value = change['new']

    def sync_prop(self, widget, prop):
        """ Sync a widget's property with the current object.

        :widget: the widget whose property is to be synced
        :prop: the property name on the widget
        :returns: None

        """
        wid = id(widget)
        self._widget_map[wid] = widget
        self._synced_props.add((wid, prop))
        widget.observe(self._observe_cb, prop)
        self.value = getattr(widget, prop)

    value = TraitType()

    @observe('value')
    def _observe_value(self, change):
        value = change['new']
        # print(f"setter called with {value}")
        for (wid, prop) in self._synced_props:
            setattr(self._widget_map[wid], prop, value)
