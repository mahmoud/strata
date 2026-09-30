
"""
An attempt at creating a somewhat holistic application configuration.

Configuration variables:

* Link database file path
* Enable/disable local file hosting
* Local file hosting root path
* Server host
* Server port
* Full host URL
* Secret key (for cookie signing)

Origins:

* Command line arguments
* Environment variables
* Config file
* code/defaults/Config kwargs
"""

import os

import pytest

from strata import Layer, ConfigSpec, ConfigException
from strata.layers import CLILayer, KwargLayer, EnvVarLayer

from .app_vars import VAR_LIST

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_LINKS_FILE_PATH = os.path.join(_CUR_PATH, 'links.txt')


class DevDefaultLayer(Layer):
    def secret_key(self):
        return 'configmanagementisimportantandhistoricallyhard'

    def link_database_path(self):
        return _DEFAULT_LINKS_FILE_PATH

    def server_host(self):
        return '0.0.0.0'

    def server_port(self):
        return 5000

    def host_url(self, server_host, server_port):
        return '%s:%s/' % (server_host, server_port)


_PROD_LAYERS = [KwargLayer, CLILayer, EnvVarLayer]
PROD_CONFIGSPEC = ConfigSpec(VAR_LIST, _PROD_LAYERS)

ProdConfig = PROD_CONFIGSPEC.make_config(name='ProdConfig')

_DEV_LAYERS = _PROD_LAYERS + [DevDefaultLayer]
DEV_CONFIGSPEC = ConfigSpec(VAR_LIST, _DEV_LAYERS)

DevConfig = DEV_CONFIGSPEC.make_config(name='DevConfig')


def test_dev_vs_prod():
    # DevConfig should work with no args
    dev_conf = DevConfig()
    assert dev_conf.host_url == '0.0.0.0:5000/'
    assert dev_conf.local_hosting_root_path == '/tmp/'
    # without dev defaults, ProdConfig should fail
    with pytest.raises(ConfigException) as exc_info:
        ProdConfig()
    assert exc_info.type is ConfigException
