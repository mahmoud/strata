# -*- coding: utf-8 -*-

import os
from argparse import ArgumentParser

from .core import Layer, Provider
from .errors import NotProvidable, MissingValue
from .utils import make_sentinel


_MISSING = make_sentinel()


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

    def __init__(self, desc=None):
        self.parser_desc = desc

    @classmethod
    def _get_provider(cls, var):
        try:
            return super(CLILayer, cls)._get_provider(var)
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
                long_name = var.var_name
            else:
                long_name = None
        return long_name, short_name

    def cli_argparser(self, config):
        # TODO: nargs?
        prs = ArgumentParser(description=self.parser_desc)
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
                    raise Exception(msg)
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

####
# Built-in Layers follow
####


class StrataConfigLayer(Layer):
    _autoprovided = ['config']

    def __init__(self, config):
        self._config = config

    def config(self):
        return self._config
