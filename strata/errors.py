# -*- coding: utf-8 -*-


class ConfigException(Exception):
    pass


class ConfigValueError(ConfigException, ValueError):
    pass


class MissingValue(ConfigValueError):
    pass


class InvalidProvider(ConfigException, TypeError):
    pass
