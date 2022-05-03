from traitlets import HasTraits, Any, Bool, observe
import ipywidgets as widgets
from IPython.display import clear_output

DEBUG=0

def D(msg):
    if DEBUG:
        print(msg)


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

def extract_operand(rhs):
    if (isinstance(rhs, tuple) and
            len(rhs) == 2 and
            (isinstance(rhs[0], HasTraits) or
             callable(rhs[0])) and
            isinstance(rhs[1], dict)):
        return rhs
    elif isinstance(rhs, HasTraits) or callable(rhs):
        return rhs, dict()
    else:
        raise ValueError(f"Invalid operand: {rhs}. Operand must be either a prop/callable, or a (prop/callable, dict)")


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
        D(f"[_notify_listeners] {self}: setter called with {value}")
        for (widget, prop) in self._output_props:
            setattr(widget, prop, value)

    def _update_self(self, new_value, trans=None):
        """ handle updates from synced props """
        # print("change received:")
        # print(change)
        if trans is not None:
            new_value = trans(new_value)
        D(f"[_update_self] {self}: setting self to {new_value}")
        self.value = new_value

    def add_input_prop(self, widget, prop='value', sync=True, trans=None):
        """ Listen to a widget's property without modifying it when our own value changes.
        parameter list is the same as sync_prop

        :sync: whether to update the current object's value according to the input prop.
            It will also update the values of all registered output props.
            Default to True.
        :trans: a transformer function for the updated value
        """
        widget.observe(lambda change: self._update_self(change['new'], trans), prop)
        self._input_props.add((widget, prop))
        if sync:
            self._update_self(getattr(widget, prop), trans)
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

    # TODO: add transformer to output prop <2022-02-10, David Deng> #
    def add_output_prop(self, widget, prop='value', sync=True):
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

    def __lshift__(self, other):
        prop, options = extract_operand(other)
        return self.add_input_prop(prop, **options)

    def __rshift__(self, other):
        prop, options = extract_operand(other)
        return self.add_output_prop(prop, **options)

    def __matmul__(self, other):
        prop, options = extract_operand(other)
        return self.sync_prop(prop, **options)

# Thought: is it possible to combine SyncedProp and ComputedProp? <2022-03-29, David Deng> #

class ComputedProp(HasTraits):
    """ a read-only prop, whose 'value' is computed based on a function and a set of input widgets.
    c1 = ComputedProp(widget, ..., f=output_function) # prop default to 'value'
    c2 = ComputedProp((widget, prop), ..., f=output_function)
    c3 = ComputedProp((widget, prop, name), ..., f=output_function)
    f should not have side effects.
    if any of the named input has a value of None, the output will also be None.
    """
    value = Any(read_only=True)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"ComputedProp(value={self.value}, inputs={self.get_named_inputs()})"

    def get_named_inputs(self):
        return { name: self._cache_values[tup] for name, tup in self._inputs.items() if tup in self._cache_values }

    def __init__(self, use_none=False):
        """ initializer.

        :inputs: input triples.
        :f: the output function
        :returns: None

        """

        self._inputs = {} # { name: (widget, prop), ... }
        self._cache_values = {} # { (widget, prop): value, ... }

        self.use_none = use_none

        f = lambda **kwargs: str(kwargs) if kwargs else None
        self.set_output(f, sync=False) # don't evaluate right now

    def update_cache(self):
        """ update the cache value by querying each of the inputs """
        # NOTE: currently remove is not supported. Invalidate the cache when input is removed <2022-02-04, David Deng> #
        for name, (widget, prop) in self._inputs.items():
            self._cache_values[(widget, prop)] = getattr(widget, prop)

    def update_value(self):
        """ update the value based on the cache """
        if not self.use_none and None in self._cache_values.values():
            D(f"None value detected in inputs of computed prop: {self.get_named_inputs()}")
            newvalue = None
        else:
            newvalue = self._f(**{ k:self._cache_values[tup] for k, tup in self._inputs.items() })
        self.set_trait('value', newvalue)

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

    def add_input(self, widget, prop="value", name=None, sync=True):
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
        D(f"registering listener on {widget}, {prop}")
        widget.observe(self._update_self, prop)
        # sync
        if sync:
            self.update_value()

        return self


    def set_output(self, f, sync=True):
        """ f takes an expanded **kwargs, """
        self._f = f
        if sync:
            self.update_value()
        return self

    def __lshift__(self, other):
        prop, options = extract_operand(other)
        return self.add_input(prop, **options)

    def __rshift__(self, other):
        # TODO: verify f is a function <2022-04-07, David Deng> #
        f, options = extract_operand(other)
        return self.set_output(f, **options)

    def __invert__(self):
        return NegatedProp(self)

    def __and__(self, other):
        return AndProp(self, other)

    def __or__(self, other):
        return OrProp(self, other)

class NegatedProp(ComputedProp):
    """ Invert the prop value """
    value = Bool(read_only=True)
    def __init__(self, p):
        super().__init__(use_none=True)
        self >> (lambda p: not p, dict(sync=False))
        self << (p, dict(name="p", sync=True))

class AndProp(ComputedProp):
    """ Invert the prop value """
    value = Bool(read_only=True)
    def __init__(self, p1, p2):
        super().__init__(use_none=True)
        self >> (lambda p1, p2: bool(p1 and p2), dict(sync=False))
        self << (p1, dict(name="p1", sync=False))
        self << (p2, dict(name="p2", sync=False))
        self.resync()

class OrProp(ComputedProp):
    """ Invert the prop value """
    value = Bool(read_only=True)
    def __init__(self, p1, p2):
        super().__init__(use_none=True)
        self >> (lambda p1, p2: bool(p1 or p2), dict(sync=False))
        self << (p1, dict(name="p1", sync=False))
        self << (p2, dict(name="p2", sync=False))
        self.resync()

########################################
#  Display-related utilities for Prop  #
########################################

def conditional_widget(cond, widget_if, widget_else=None):
    """ An interactive widget that only gets displayed when cond evaluates to True """
    # TODO: remove the padding? <2022-04-13, David Deng> #
    out = widgets.Output()
    out.add_class("no-subarea-padding")
    # .no-subarea-padding .output_subarea {
    #     padding: 0 !important;
    # }
    def observer(_):
        with out:
            clear_output()
            if cond.value:
                display(widget_if)
            elif widget_else is not None:
                display(widget_else)
    cond.observe(observer, 'value')
    observer(None)
    return out

def display_with_style(obj, label=None):
    """Display obj and label with styles
    """
    w = widgets.HTML()
    # TODO: add classes for styles <2022-03-31, David Deng> #
    if isinstance(obj, list):
        obj = tabulate([["", item] for item in obj], tablefmt="html")
        w.add_class("hide-first-column")
        # .hide-first-column td:first-child {
        #     display: none;
        # }
    elif isinstance(obj, dict):
        obj = tabulate([[k,v] for k,v in obj.items()], tablefmt="html")

    w.add_class("fancy-table")
    if label:
        w.value = f"<p><b>{label}</b>: {obj}</p>"
    else:
        w.value = f"<p>{obj}</p>"
    display(w)

def displayable(prop, label=None):
    def f(obj):
        display_with_style(obj, label)
    return widgets.interactive_output(f, {"obj": prop})
