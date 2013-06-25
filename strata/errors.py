# -*- coding: utf-8 -*-


class ConfigException(Exception):
    pass


class ParseError(ConfigException):
    pass


class MissingValueError(ConfigException):
    pass
