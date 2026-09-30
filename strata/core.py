import inspect
import types

from boltons.strutils import camel2under, under2camel

from .utils import get_arg_names
from .errors import ProviderError, NotProvidable


class VariableMeta(type):
    def __new__(mcls, name, bases, attrs):
        n_attr = attrs.get('name')
        if not n_attr:
            n_attr = attrs['name'] = camel2under(name)
        if n_attr.startswith('_'):
            msg = 'Variable name cannot start with underscore: %r' % n_attr
            raise TypeError(msg)
        cls = super().__new__(mcls, name, bases, attrs)

        cls.description = getattr(cls, 'description', '') or cls.__doc__ or ''
        default_summary = (cls.description.splitlines() or [''])[0][:60]
        cls.summary = getattr(cls, 'summary', '') or default_summary

        return cls


class Variable(metaclass=VariableMeta):
    name = None
    validator = None

    def process_value(self, value):
        if self.validator:
            return self.validator(value)
        return value


class Layer:
    @classmethod
    def _get_provider(cls, variable):
        vn = variable.name
        try:
            func = getattr(cls, vn)
        except AttributeError:
            raise NotProvidable(cls, variable) from None
        if not callable(func):
            raise NotProvidable(cls, variable, f'{vn!r} is not callable')
        return Provider(cls, vn, func)

    @classmethod
    def _get_autoprovided(cls):
        """
        returns Variable instances for automatically provided
        variables within a Layer.
        """
        cn = cls.__name__
        # get explicit autoprovides
        eap = getattr(cls, '_autoprovided', [])
        ap_var_map, unknown_eaps = {}, []
        for obj in eap:
            try:
                if issubclass(obj, Variable):
                    ap_var_map[obj.name] = obj
                    continue
            except TypeError:
                pass
            if isinstance(obj, str):
                ap_var_map[obj] = None
            else:
                unknown_eaps.append(obj)
        if unknown_eaps:
            raise TypeError('Layer %s has unsupported autoprovide types: %r'
                            % (cn, unknown_eaps))

        for attrname in dir(cls):
            if attrname in ap_var_map and ap_var_map[attrname] is not None:
                continue  # already has a variable associated with it
            attr = getattr(cls, attrname)
            try:
                auto_var = attr._autoprovided_variable
            except AttributeError:
                if attrname in ap_var_map and inspect.isfunction(attr):
                    auto_var = func2variable(attr)
                else:
                    continue
            ap_var_map[attrname] = auto_var

        unconverted = [an for an, var in ap_var_map.items() if var is None]
        if unconverted:
            raise TypeError('unable to resolve %s autoprovided variables: %r'
                            % (cn, unconverted))
        return list(ap_var_map.values())

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Provider:
    """\
    Used internally to represent a single Layer instance's implementation
    of a single Variable. (the intersection of Layer and Variable).
    """

    def __init__(self, layer, var_name, func):
        if isinstance(layer, type):
            self.layer_inst = None
            self.layer_type = layer
        else:
            self.layer_inst = layer
            self.layer_type = type(layer)
        self.var_name = var_name
        self.func = func
        try:
            self.dep_names = get_arg_names(self.func)
        except TypeError as e:
            raise ProviderError('unsupported provider type: %r' % self.func) from e
        # A plain function defined on the Layer class is an unbound
        # method: its first positional parameter is ``self``, not a
        # dependency. get_bound() rebinds it to the Layer instance.
        # (getattr_static sees through staticmethod/classmethod.)
        self._is_unbound_method = (
            inspect.isfunction(func)
            and inspect.getattr_static(self.layer_type, var_name, None) is func)
        if self._is_unbound_method:
            self.dep_names = self.dep_names[1:]

    @property
    def is_bound(self):
        return self.layer_inst is not None

    def get_bound(self, layer_inst):
        if not isinstance(layer_inst, self.layer_type):
            raise TypeError('expected an instance of %r, not %r'
                            % (self.layer_type, layer_inst))
        if self._is_unbound_method:
            func = types.MethodType(self.func, layer_inst)
        else:
            func = self.func
        return type(self)(layer_inst, self.var_name, func)

    def __repr__(self):
        cn = self.__class__.__name__
        try:
            layer_cn = self.layer_type.__name__
            func_sig = '%s(%s)' % (self.var_name, ', '.join(self.dep_names))
            return '%s(%s.%s)' % (cn, layer_cn, func_sig)
        except AttributeError:
            return super().__repr__()


def ez_vars(layers):
    """
    A (most likely temporary) utility function to make Variables off
    of Layer definitions. Something like this should maybe exist in
    the future, using decorators.
    """
    names = set()
    for layer in layers:
        for name in dir(layer):
            if name.startswith('_'):
                continue
            names.add(under2camel(name))
    return [VariableMeta(n, (Variable,), {}) for n in sorted(names)]


def func2variable(func, class_name=None, **kwargs):
    "expects a function, not a bound/unbound method."
    var_name = func.__name__
    class_name = class_name or under2camel(var_name)
    attrs = dict(kwargs, name=var_name)
    attrs.setdefault('description', func.__doc__)
    variable = VariableMeta(class_name, (Variable,), attrs)
    return variable


def autoprovide(*args, **kwargs):
    attrs = {'validator': kwargs.pop('validator', None),
             'description': kwargs.pop('description', None),
             'summary': kwargs.pop('summary', None)}
    if kwargs:
        raise TypeError('got unexpected keyword arguments: %r' % list(kwargs))
    attrs = {k: v for k, v in attrs.items() if v is not None}

    def autoprovide_attr_assigner(func):
        variable = func2variable(func, **attrs)
        func._autoprovided_variable = variable
        return func

    if args:
        func = args[0]
        if callable(func):
            return autoprovide_attr_assigner(func)
        else:
            raise TypeError('autoprovide expects to be called as a decorator'
                            ' on a function, not %r' % func)
    else:
        return autoprovide_attr_assigner
