import sys

from strata.core import Variable, ez_vars
from strata.config import ConfigSpec
from strata.layers import CLILayer, KwargLayer


class VarOne(Variable):
    "the best variable, it is known"
    cli_arg_name = 'one'
    is_config_kwarg = True


class VarTwo(Variable):
    cli_arg_name = 'two'


def get_cli_config_spec(layers=None):
    layers = layers or [KwargLayer, CLILayer]
    variables = [VarOne, VarTwo] + ez_vars(layers)
    return ConfigSpec(variables, layers)


def test_cli(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog', '--two', 'testingMEH'])
    TestConfig = get_cli_config_spec().make_config()
    config = TestConfig(var_one='var_one is #1! USA! USA!')
    assert 'var_one' in repr(config)
    assert config.var_one == 'var_one is #1! USA! USA!'
    assert config.var_two == 'testingMEH'
    assert '--one' in config.cli_help
    assert 'the best variable' in config.cli_help
    assert config.cli_help_summary.startswith('usage:')
