from traitlets import HasTraits, Any, observe

def is_list_unpackable(obj):
    try:
        (lambda *a: None)(*obj)
    except TypeError:
        return False
    return True

def is_dict_unpackable(obj):
    try:
        (lambda **a: None)(**obj)
    except TypeError:
        return False
    return True

class Prop(HasTraits):
    """ Simple Prop with a 'value' attribute. """
    value = Any()
    def __init__(self, value=None):
        self.value = value

class SyncedProp(HasTraits):
    """ Single synced prop to multiple widgets
    s1 = SyncedProp(widget, ..., value=None) # prop default to 'value'
    s2 = SyncedProp((widget, prop), ..., value=None)
    """

    value = Any()

    def __init__(self, *args, value=None):
        """ args is a list of 2-tuples (widget, prop) or widget """
        # TODO: use a list to store the props and use index to identify each prop? <2022-03-24, David Deng> #
        self._output_props = set() # a set of (widget, prop), only update their values
        self._input_props = set() # a set of (widget, prop), only listen to their updates
        self.value = value

        for i in args:
            if is_list_unpackable(i):
                self.sync_prop(*i)
            else:
                self.sync_prop(i)

    @observe('value')
    def _notify_listeners(self, change):
        """ handle programmatic change on 'value' """
        value = change['new']
        # print(f"setter called with {value}")
        for (widget, prop) in self._output_props:
            setattr(widget, prop, value)

    def _update_self(self, change):
        """ handle updates from synced props """
        # print("change received:")
        # print(change)
        self.value = change['new']

    # TODO: add transformer to input and output prop <2022-02-10, David Deng> #
    def add_input_prop(self, widget, prop='value', sync=True):
        """ Listen to a widget's property without modifying it when our own value changes.
        parameter list is the same as sync_prop

        :sync: whether to update the current object's value according to the input prop.
            It will also update the values of all registered output props.
            Default to True.
        """
        widget.observe(self._update_self, prop)
        self._input_props.add((widget, prop))
        if sync:
            self.value = getattr(widget, prop)
        return self

    # def resync(self):
    #     """ resync the value attribute """
    #     value = None
    #     for (widget, prop) in self._input_props:
    #         # TODO: define the semantics of this function <2022-03-04, David Deng> #
    #         # assert all inputs have the same value?
    #         # future: name each input element, and sync based on a specific input, if they are not all equal
    #         # can use itertools.groupby https://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical
    #         # <2022-03-04, David Deng> #
    #         value = ...
    #         pass
    #     self._update_self(value)

    def add_output_prop(self, widget, prop='value', sync=False):
        """ Listen to a widget's property without modifying it when our own value changes.
        parameter list is the same as sync_prop

        :sync: whether to sync the current object's value to the output prop.
            Default to False.
        """
        self._output_props.add((widget, prop))
        if sync:
            setattr(widget, prop, self.value)
        return self

    def sync_prop(self, widget, prop='value', source='prop'):
        """ Sync a widget's property with the current object.

        :widget: the widget whose property is to be synced
        :prop: the property name on the widget
        :source: the source of initialization, can be 'self', 'prop', or 'none'
            'self' means update the registered prop value according to this object's value
            'prop' means update this object's value according to the registerd prop value
            'none' means don't update the value, but only register listeners on both objects.
        :returns: None

        """
        sync_input = False
        sync_output = False
        if source == 'prop':
            sync_input = True
        elif source == 'self':
            sync_output = True
        elif source == 'none':
            pass
        else:
            raise ValueError("The source parameter must be one of 'self', 'prop', or 'none'.")

        self.add_input_prop(widget, prop, sync=sync_input)
        self.add_output_prop(widget, prop, sync=sync_output)
        return self

class ComputedProp(HasTraits):
    """ a read-only prop, whose 'value' is computed based on a function and a set of input widgets.
    c1 = ComputedProp(widget, ..., f=output_function) # prop default to 'value'
    c2 = ComputedProp((widget, prop), ..., f=output_function)
    c3 = ComputedProp((widget, prop, name), ..., f=output_function)
    f should not have side effects.
    if any of the named input has a value of None, the output will also be None.
    """
    # TODO: The None propagation can be inconvenient when we want to cast to a boolean <2022-03-19, David Deng> #

    value = Any(read_only=True)

    def __str__(self):
        return f"ComputedProp(value={self.value}, inputs={self.get_named_inputs()})"

    def get_named_inputs(self):
        return { name: self._cache_values[tup] for name, tup in self._inputs.items() if tup in self._cache_values }

    def __init__(self, *inputs, f=None, use_none=False):
        """ initializer.

        :inputs: input triples.
        :f: the output function
        :returns: TODO

        """
        if f is None:
            f = lambda **kwargs: str(kwargs) if kwargs else None
        self.set_output(f)

        self._inputs = {} # { name: (widget, prop), ... }
        self._cache_values = {} # { (widget, prop): value, ... }

        self.use_none = use_none

        # if not inputs:
        #     raise ValueError("ComputedProp must be initialized with at least one input tuple or triple.")

        self.add_inputs(*inputs)

    def update_cache(self):
        """ update the cache value by querying each of the inputs """
        # TODO: currently remove is not supported. Invalidate the cache when input is removed <2022-02-04, David Deng> #
        for name, (widget, prop) in self._inputs.items():
            self._cache_values[(widget, prop)] = getattr(widget, prop)

    def update_value(self):
        """ update the value based on the cache """
        if not self.use_none and None in self._cache_values.values():
            # TODO: add debug flag <2022-03-01, David Deng> #
            # print(f"None value detected in inputs of computed prop: {self.get_named_inputs()}")
            newvalue = None
        else:
            newvalue = self._f(**{ k:self._cache_values[tup] for k, tup in self._inputs.items() })
        self.set_trait('value', newvalue)

    # TODO: rename to sync, add to SyncedProp as well <2022-03-01, David Deng> #
    def resync(self):
        """ resync the value attribute """
        self.update_cache()
        self.update_value()
        return self

    def _update_self(self, change):
        """ handle updates from synced props """
        # print("change received:")
        # print(change)
        widget = change['owner']
        prop = change['name']
        h = (widget, prop)
        # only update cache if the property is named
        if h in self._cache_values:
            assert self._cache_values[h] == change['old'], \
                f"Previous cache value {self._cache_values[h]} inconsistent with change description {change['old']}"
            self._cache_values[h] = change['new']
        self.update_value()

    def add_input(self, widget, prop="value", name=None, sync=False):
        """ add a widget's property with the current object.

        :widget: the widget whose property is to be taken as an input
        :prop: the property name on the widget
        :name: the name of the input to be referred to in set_output's function,
                if None, it will not be passed to the output function,
                but still used to trigger value update when its value changes.
        :returns: self

        """
        # only record the value in cache if the input is named
        if name is not None:
            self._inputs[name] = (widget, prop)
            # avoid triggering widget getter multiple times
            h = (widget, prop)
            self._cache_values[h] = getattr(widget, prop)
        # TODO: turn this into debug flag <2022-03-01, David Deng> #
        # print(f"registering listener on {widget}, {prop}")
        widget.observe(self._update_self, prop)
        # sync
        if sync:
            self.update_value()

        return self

    def add_inputs(self, *inputs, sync=True):
        for i in inputs:
            if not is_list_unpackable(i):
                # if i is not a tuple, it is a widget, prop default to 'value'
                widget = i
                i = (widget, 'value')
            # don't update yet, because haven't added all inputs
            self.add_input(*i, sync=False)
        if sync:
            self.update_value()
        return self

    def set_output(self, f):
        """ f takes an expanded **kwargs, """
        self._f = f
        return self
