# -*- coding: utf-8 -*-


class ConfigException(Exception):
    pass


class ConfigValueError(ConfigException, ValueError):
    pass


class MissingValue(ConfigValueError):
    pass


class InvalidValue(ConfigValueError):
    pass


class LayerError(ConfigException, TypeError):
    pass


class ProviderError(ConfigException, TypeError):
    pass
