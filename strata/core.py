# -*- coding: utf-8 -*-

from utils import under2camel, camel2under, get_arg_names

_KNOWN_VARS = {}


class VariableMeta(type):
    def __new__(cls, name, base, attrs):
        if not attrs.get('name'):
            attrs['name'] = camel2under(name)
        inst = super(VariableMeta, cls).__new__(cls, name,  base, attrs)

        if inst.name in _KNOWN_VARS:
            print 'config variable collision: %r' % inst.name
        _KNOWN_VARS[inst.name] = inst
        return inst


class Variable(object):
    "default Variable class description docstring."
    __metaclass__ = VariableMeta

    name = None
    var_type = None  # TODO?
    short_desc = "default Variable class short description"

    is_cli_arg = False  # TODO?
    is_config_param = False

    def get_default(self, config):
        raise KeyError('no default specified for: %s' % self.name)

    def validate(self, config):
        pass  # TODO


def ez_vars(layerset):
    """
    A (most likely temporary) utility function to make Variables off
    of Layer definitions. Something like this should maybe exist in
    the future, using decorators.
    """
    names = set()
    for layer in layerset.layers:
        for name in dir(layer):
            if name.startswith('_'):
                continue
            if name == 'layer_provides':
                continue  # TODO: tmp
            names.add(under2camel(name))
    return [VariableMeta(n, (Variable,), {}) for n in sorted(names)]


class Layer(object):
    @classmethod
    def _get_provider(cls, variable):
        # TODO: descriptor to support usage on both class and instance?
        # TODO: switch to getattribute?
        return Provider(cls, variable.name)

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class StrataLayer(Layer):
    def __init__(self, config):
        self._config = config

    def config(self):
        return self._config


class LayerSet(object):
    def __init__(self, env_name, layers):
        # TODO: assert all Layers are unique types?
        self.env_name = env_name
        self.layers = list(layers)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r)' % (cn, self.env_name, self.layers)

    def __iter__(self):
        return iter(self.layers)

    def __getitem__(self, key):
        return self.layers.__getitem__(key)


class Provider(object):
    """\
    Used internally to represent a single Layer instance's implementation
    of a single Variable. (the intersection of Layer and Variable).
    """

    def __init__(self, layer, var_name, func=None):
        if isinstance(layer, type):
            self.layer_inst = None
            self.layer_type = layer
        else:
            self.layer_inst = layer
            self.layer_type = type(layer)
        self.var_name = var_name
        self.func = func
        if self.func is None:
            self._set_func(layer)
        else:
            self._is_custom_func = True

    def _set_func(self, layer):
        self._is_custom_func = False
        vn = self.var_name
        try:
            self.func = getattr(layer, vn)
        except AttributeError:
            raise ValueError("Layer %r doesn't provide %r" % (layer, vn))
        try:
            self.dep_names = get_arg_names(self.func)
        except:
            raise ValueError('unsupported provider type: %r' % self.func)

    @property
    def is_bound(self):
        return self.layer_inst is not None

    def get_bound(self, layer_inst):
        # TODO: check that layer types match?
        p_type = type(self)
        func = self.func if self._is_custom_func else None
        return p_type(layer_inst, self.var_name, func)

    def __repr__(self):
        cn = self.__class__.__name__
        try:
            layer_cn = self.layer_type.__name__
            func_sig = '%s(%s)' % (self.var_name, ', '.join(self.dep_names))
            return '%s(%s.%s)' % (cn, layer_cn, func_sig)
        except:
            return super(Provider, self).__repr__()


class FileValue(object):
    def __init__(self, value, file_path):
        self.value = value
        self.file_path = file_path


if __name__ == '__main__':
    class MyVar(Variable):
        pass

    print MyVar.name
