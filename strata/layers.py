# -*- coding: utf-8 -*-

from argparse import ArgumentParser

from core import Layer, Provider
from errors import ProviderError
from utils import make_sentinel


_MISSING = make_sentinel()


class KwargLayer(Layer):
    @classmethod
    def _get_provider(cls, variable):
        if not getattr(variable, 'is_config_kwarg', None):
            raise ProviderError('not a config kwarg: %r' % variable)

        def _get_config_kwarg(config):
            return config.kwargs[variable.name]

        return Provider(cls, variable.name, _get_config_kwarg)


class CLILayer(Layer):
    _allowed_actions = ('store', 'append', 'count')

    def __init__(self, desc=None):
        self.parser_desc = desc

    @classmethod
    def _get_provider(cls, var):
        try:
            return super(CLILayer, cls)._get_provider(var)
        except ProviderError as pe:
            pass
        arg_name, short_arg_name = cls._get_cli_arg_names(var)
        if arg_name or short_arg_name:
            var_getter = cls._make_parsed_arg_getter(var.name)
            return Provider(cls, var.name, var_getter)
        raise pe

    @classmethod
    def _make_parsed_arg_getter(cls, var_name):
        def _get_parsed_arg(parsed_args):
            return getattr(parsed_args, var_name)
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

    def argparser(self, config):
        # TODO: nargs?
        prs = ArgumentParser(description=self.parser_desc)
        for var in config.config_spec.variables:
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

    def parsed_args(self, argparser):
        return argparser.parse_known_args()[0]

    def cli_help_summary(self, argparser):
        return argparser.format_usage()

    def cli_help(self, argparser):
        return argparser.format_help()
