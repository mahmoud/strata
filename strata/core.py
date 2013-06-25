# -*- coding: utf-8 -*-

from utils import camel2under

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
    # TODO
    provides = ()


class FileValue(object):
    def __init__(self, value, file_path):
        self.value = value
        self.file_path = file_path


if __name__ == '__main__':
    class MyVar(Variable):
        pass

    print MyVar.name
