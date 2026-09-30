

class ConfigException(Exception):
    pass


class ConfigValueError(ConfigException, ValueError):
    pass


class MissingValue(ConfigValueError):
    pass


class InvalidValue(ConfigValueError):
    pass


class LayerError(ConfigException):
    """
    Raised by a Layer's provider to abort Config processing outright,
    instead of being recorded as Unsatisfied and falling through to the
    next Layer (which is what any other exception does). Use it for
    problems that are never fixable by a lower Layer, e.g. a malformed
    config file.
    """


class ProviderError(ConfigException, TypeError):
    pass


class NotProvidable(ConfigException):
    """
    This type of Exception is raised at ConfigSpec-creation time to
    indicate that a given Layer does not provide a given variable.
    """
    def __init__(self, layer_type, variable_type, details=None):
        msg = '%s does not provide %s (%s)' % (layer_type.__name__,
                                               variable_type.name,
                                               variable_type.__name__,)
        if details:
            msg += ': %s' % (details,)
        super().__init__(msg)


class ConfigSpecException(Exception):
    pass


class DependencyCycle(ConfigSpecException):
    pass


class UnresolvedDependency(ConfigSpecException):
    pass
