
class SyncedProp:
    """single synced prop to multiple widgets"""
    # TODO: Inherit from HasTrait? See https://traitlets.readthedocs.io/en/stable/api.html#callbacks-when-trait-attributes-change<2022-02-03, David Deng> #

    def __init__(self, *args):
        """ args is a list of 2-tuples (widget, prop) """
        self._value = None
        self._widget_map = {}  # from id -> widget
        self._synced_props = set()
        self._listeners = []
        for (widget, prop) in args:
            self.sync_prop(widget, prop)

    def _observe_cb(self, change):
        # When the value changes, update the internal model
        print("change received:")
        print(change)
        self.value = change['new']

    def sync_prop(self, widget, prop):
        # add new items to map and props, add listeners
        # assume widget is registered
        wid = id(widget)
        self._widget_map[wid] = widget
        self._synced_props.add((wid, prop))
        widget.observe(self._observe_cb, prop)
        self.value = getattr(widget, prop)

    def observe(self, listener, k):
        """ compliant with standard widget interface, so that it can be used in interactive_output """
        if k != 'value':
            raise KeyError(
                "Invalid key: {k}. SyncedProp does not have properties other than 'value'")
        self._listeners.append(listener)

    @property
    def value(self):
        print("getter called")
        return self._value

    @value.setter
    def value(self, value):
        print(f"setter called with {value}")
        for (wid, prop) in self._synced_props:
            setattr(self._widget_map[wid], prop, value)
        for listener in self._listeners:
            change = {'name': 'value', 'old': self._value,
                      'new': value, 'owner': self, 'type': 'change'}
            print("emitting change: {}".format(change))
            listener(change)
        self._value = value
