from traitlets import HasTraits, Any, observe

class SyncedProp(HasTraits):
    """single synced prop to multiple widgets"""

    value = Any()

    def __init__(self, *args):
        """ args is a list of 2-tuples (widget, prop) """
        self._widget_map = {} # from id -> widget
        self._synced_props = set() # a set of (id, prop), bidirectional updates
        for (widget, prop) in args:
            self.sync_prop(widget, prop)

    @observe('value')
    def _observe_value(self, change):
        """ handle programmatic change on 'value' """
        value = change['new']
        # print(f"setter called with {value}")
        for (wid, prop) in self._synced_props:
            setattr(self._widget_map[wid], prop, value)

    def _observe_cb(self, change):
        """ handle updates from synced props """
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

class ComputedProp(HasTraits):
    """ a read-only prop, whose 'value' is computed based on a function and a set of input widgets. """

    value = Any(read_only=True)

    def __init__(self, *inputs, f=None):
        """ initializer.

        :inputs: input triples.
        :f: the output function
        :returns: TODO

        """
        if f is None:
            f = lambda **kwargs: str(kwargs)
        self.set_output(f)

        self._inputs = {} # { name: (widget, prop), ... }
        self._cache_values = {} # { hash(widget, prop): value, ... }
        if not inputs:
            raise ValueError("ComputedProp must be initialized with at least one input triple.")
        for i in inputs:
            try:
                name, widget, prop = i
            except:
                raise ValueError(f"input {i} cannot be unpacked to a triple.")
            self.add_input(name, widget, prop)
        self.update_value()

    def update_cache(self):
        """ update the cache value by querying each of the inputs """
        # TODO: currently remove is not supported. Invalidate the cache when input is removed <2022-02-04, David Deng> #
        for name, (widget, prop) in self._inputs.items():
            self._cache_values[hash((widget, prop))] = getattr(widget, prop)

    def update_value(self):
        """ update the value based on the cache """
        self.set_trait('value', self._f(**{ k:self._cache_values[hash(tup)] for k, tup in self._inputs.items() }))

    def resync(self):
        """ resync the value attribute """
        self.update_cache()
        self.update_value()

    def _observe_cb(self, change):
        """ handle updates from synced props """
        # print("change received:")
        # print(change)
        widget = change['owner']
        prop = change['name']
        h = hash((widget, prop))
        assert self._cache_values[h] == change['old'], \
            f"Previous cache value {self._cache_values[h]} inconsistent with change description {change['old']}"
        self._cache_values[h] = change['new']
        self.update_value()


    def add_input(self, name, widget, prop):
        """ add a widget's property with the current object.

        :name: the name of the input to be referred to in set_output's function
        :widget: the widget whose property is to be taken as an input
        :prop: the property name on the widget
        :returns: None

        """
        self._inputs[name] = (widget, prop)
        # avoid triggering widget getter multiple times
        h = hash((widget, prop))
        self._cache_values[h] = getattr(widget, prop)
        widget.observe(self._observe_cb, prop)

    def set_output(self, f):
        """ f takes an expanded **kwargs, """
        self._f = f
