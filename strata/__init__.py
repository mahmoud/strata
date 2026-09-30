"""strata: layered, dependency-resolving application configuration."""

__version__ = '26.0.1dev'

from .core import Variable, Layer, Provider
from .config import ConfigSpec
from .errors import (ConfigException, ConfigSpecException, LayerError,
                     MissingValue, NotProvidable)
from .layers import (CLILayer, KwargLayer, EnvVarLayer,
                     TOMLFileLayer, ConfigFilePath)

__all__ = ['Variable', 'Layer', 'Provider', 'ConfigSpec',
           'ConfigException', 'ConfigSpecException', 'LayerError', 'MissingValue',
           'NotProvidable',
           'CLILayer', 'KwargLayer', 'EnvVarLayer', 'TOMLFileLayer', 'ConfigFilePath']
