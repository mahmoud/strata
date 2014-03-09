# -*- coding: utf-8 -*-

from strata import Variable


class HostURL(Variable):
    name = 'host_url'
    cli_arg_name = 'host_url'
    is_config_kwarg = True


class LinkDatabasePath(Variable):
    cli_arg_name = 'db_path'
    is_config_kwarg = True


class LocalHostingRootPath(Variable):
    cli_arg_name = 'local_root'
    is_config_kwarg = True
    default_value = '/tmp/'


class ServerHost(Variable):
    cli_arg_name = 'host'
    is_config_kwarg = True


class ServerPort(Variable):
    cli_arg_name = 'port'
    is_config_kwarg = True
    json_config_key = 'port'


class SecretKey(Variable):
    env_var_name = 'EROSION_KEY'


VAR_LIST = [LinkDatabasePath, LocalHostingRootPath,
            ServerHost, ServerPort, HostURL, SecretKey]
