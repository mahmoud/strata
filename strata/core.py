# -*- coding: utf-8 -*-


class Config(object):
    pass  # TODO


class Variable(object):
    "default Variable class description docstring."

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
