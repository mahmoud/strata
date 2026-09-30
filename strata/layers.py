
import os
from argparse import ArgumentParser

from boltons.typeutils import make_sentinel

from .core import Layer, Provider, Variable
from .errors import NotProvidable, MissingValue, LayerError

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib


_MISSING = make_sentinel('_MISSING')


class KwargLayer(Layer):
    _helpstr = 'expects `is_config_kwarg` to be set on Variable'

    @classmethod
    def _get_provider(cls, var):
        if not getattr(var, 'is_config_kwarg', None):
            raise NotProvidable(cls, var, cls._helpstr)

        def _get_config_kwarg(config):
            return config._input_kwargs[var.name]

        return Provider(cls, var.name, _get_config_kwarg)


class EnvVarLayer(Layer):
    _helpstr = 'expects `env_var_name` to be set on Variable'

    @classmethod
    def _get_provider(cls, var):
        env_var_name = getattr(var, 'env_var_name', None)
        if not env_var_name:
            raise NotProvidable(cls, var, cls._helpstr)

        def _get_env_var():
            ret = os.getenv(env_var_name)
            if ret is None:
                raise MissingValue('no value set for environment variable: %r'
                                   ' (for %s)' % (env_var_name, var.__name__))
            return ret

        return Provider(cls, var.name, _get_env_var)


class CLILayer(Layer):
    _helpstr = 'expects `is_cli_arg` or `cli_arg_name` to be set on Variable'
    _allowed_actions = ('store', 'append', 'count')

    # TODO
    _autoprovided = ['cli_argparser', 'cli_parsed_args', 'cli_help',
                     'cli_help_summary']
    _parser_desc = ''

    @classmethod
    def _get_provider(cls, var):
        try:
            return super()._get_provider(var)
        except NotProvidable:
            pass
        arg_name, short_arg_name = cls._get_cli_arg_names(var)
        if arg_name or short_arg_name:
            var_getter = cls._make_parsed_arg_getter(var.name)
            return Provider(cls, var.name, var_getter)
        raise NotProvidable(cls, var, cls._helpstr)

    @classmethod
    def _make_parsed_arg_getter(cls, var_name):
        def _get_parsed_arg(cli_parsed_args):
            ret = getattr(cli_parsed_args, var_name)
            if ret is None:
                raise MissingValue(var_name)
            return ret
        return _get_parsed_arg

    @staticmethod
    def _get_cli_arg_names(var):
        is_cli_arg = getattr(var, 'is_cli_arg', None)
        long_name = getattr(var, 'cli_arg_name', None)
        short_name = getattr(var, 'cli_short_arg_name', None)
        if not (long_name or short_name):
            if is_cli_arg:
                long_name = var.name
            else:
                long_name = None
        return long_name, short_name

    def cli_argparser(self, config):
        # TODO: nargs?
        prs = ArgumentParser(description=self._parser_desc)
        for var in config._config_spec.variables:
            arg_name, short_arg_name = self._get_cli_arg_names(var)
            if not arg_name and not short_arg_name:
                continue
            action = getattr(var, 'cli_action', _MISSING)
            const = getattr(var, 'cli_const', _MISSING)
            norf = []
            if arg_name:
                norf.append('--' + arg_name)
            if short_arg_name:
                norf.append('-' + short_arg_name)
            kwargs = {'dest': var.name,
                      'required': False}
            if action is _MISSING:
                action = 'store'
            else:
                if action not in self._allowed_actions:
                    msg = ('unrecognized CLI action: %r (expected one of %r)' %
                           (action, self._allowed_actions))
                    raise ValueError(msg)
            if const is not _MISSING and action != 'count':
                kwargs['action'] = '%s_const' % action
                kwargs['const'] = const
            else:
                kwargs['action'] = action
            kwargs['help'] = var.summary
            prs.add_argument(*norf, **kwargs)
        return prs

    def cli_parsed_args(self, cli_argparser):
        return cli_argparser.parse_known_args()[0]

    def cli_help_summary(self, cli_argparser):
        return cli_argparser.format_usage()

    def cli_help(self, cli_argparser):
        return cli_argparser.format_help()


class ConfigFilePath(Variable):
    """Path to the TOML config file read by TOMLFileLayer. Pass it as a
    Config kwarg or ``--config-file``, or subclass to add a default::

        class AppConfigFilePath(ConfigFilePath):
            name = 'config_file_path'  # subclasses get a new name otherwise
            default_value = '/etc/app/config.toml'
    """
    is_config_kwarg = True
    cli_arg_name = 'config-file'


class TOMLFileLayer(Layer):
    """Provides Variables with `config_key` (dotted path, e.g. 'server.port')
    or `is_config_key = True` (key = Variable.name at top level) from the
    TOML document at the `config_file_path` Variable."""
    _helpstr = 'expects `config_key` or `is_config_key` to be set on Variable'
    _autoprovided = ['toml_config_data']

    @classmethod
    def _get_provider(cls, var):
        try:
            return super()._get_provider(var)
        except NotProvidable:
            pass
        key = getattr(var, 'config_key', None)
        if not key and getattr(var, 'is_config_key', False):
            key = var.name
        if not key:
            raise NotProvidable(cls, var, cls._helpstr)

        def _get_toml_value(toml_config_data):
            cur = toml_config_data
            for part in key.split('.'):
                if not isinstance(cur, dict) or part not in cur:
                    raise MissingValue(f'no value at {key!r} in config file'
                                       f' (for {var.__name__})')
                cur = cur[part]
            return cur

        return Provider(cls, var.name, _get_toml_value)

    def toml_config_data(self, config_file_path):
        try:
            with open(config_file_path, 'rb') as f:
                return tomllib.load(f)
        except FileNotFoundError as e:
            raise MissingValue(f'config file not found: {config_file_path!r}') from e
        except tomllib.TOMLDecodeError as e:
            # a broken file is never fixable by a lower layer; abort
            raise LayerError(f'invalid TOML in {config_file_path!r}: {e}') from e


"""
Built-in Layers sandwich user-provided layers, with StrataConfigLayer
providing the top-level 'config' object representing the instance
currently being populated, and StrataDefaultLayer handling any
Variables intrinsic defaults.

StrataConfigLayer is always the first layer and StrataDefaultLayer is
always the last layer.
"""


class StrataConfigLayer(Layer):
    _autoprovided = ['config']

    def __init__(self, config):
        self._config = config

    def config(self):
        return self._config


class StrataDefaultLayer(Layer):
    _helpstr = 'expects `default_value` to be set on Variable'

    @classmethod
    def _get_provider(cls, var):
        # TODO: consider allowing a get_default() function
        if not hasattr(var, 'default_value'):
            raise NotProvidable(cls, var, cls._helpstr)

        def _get_default_value():
            return var.default_value

        return Provider(cls, var.name, _get_default_value)
