# -*- coding: utf-8 -*-

from utils import camel2under, get_arg_names

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


class Layer(object):
    def layer_provides(self):
        # TODO: name?
        # TODO: memoize?
        members = [(name, getattr(self, name)) for name in dir(self)]
        return dict([(name, func) for name, func in members
                     if callable(func) and name[:1] != '_'
                     and name != 'layer_provides'])

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Provider(object):
    """\
    Used internally to represent a single Layer instance's implementation
    of a single Variable. (the intersection of Layer and Variable).
    """

    def __init__(self, layer, var_name, func=None):
        self.layer = layer
        self.var_name = var_name
        self.func = func
        if self.func is None:
            try:
                self.func = getattr(layer, var_name)
            except AttributeError:
                msg = 'Layer %r does not provide %r' % (layer, var_name)
                raise ValueError(msg)
        try:
            self.dep_names = get_arg_names(self.func)
        except:
            raise ValueError('unsupported provider type: %r' % self.func)

    def __repr__(self):
        cn = self.__class__.__name__
        try:
            layer_cn = self.layer.__class__.__name__
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
