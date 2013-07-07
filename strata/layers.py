# -*- coding: utf-8 -*-

from argparse import ArgumentParser

from core import Layer, Provider


class CLILayer(Layer):
    def __init__(self, desc=None):
        self.parser_desc = desc

    @classmethod
    def _get_provider(cls, variable):
        try:
            return super(CLILayer, cls)._get_provider(variable)
        except ValueError:
            var_getter = cls._make_parsed_arg_getter(variable.name)
            return Provider(cls, variable.name, var_getter)

    @classmethod
    def _make_parsed_arg_getter(cls, var_name):
        def _get_parsed_arg(parsed_args):
            kwargs, pos = parsed_args
            return getattr(kwargs, var_name)
        return _get_parsed_arg

    def argparser(self, config):
        # TODO: nargs?
        prs = ArgumentParser(description=self.parser_desc)
        for var in config.config_spec.variables:
            is_cli_arg = getattr(var, 'is_cli_arg', None)
            arg_name = getattr(var, 'cli_arg_name', None)
            short_arg_name = getattr(var, 'cli_short_arg_name', None)
            action = getattr(var, 'cli_action', None)  # store, append, count
            const = getattr(var, 'cli_const', None)
            if not (arg_name or short_arg_name):
                if is_cli_arg:
                    arg_name = var.var_name
                else:
                    continue
            norf = []
            if arg_name:
                norf.append('--' + arg_name)
            if short_arg_name:
                norf.append('-' + short_arg_name)
            prs.add_argument(*norf, dest=var.name, required=False)
        return prs

    def parsed_args(self, argparser):
        return argparser.parse_known_args()[0]
