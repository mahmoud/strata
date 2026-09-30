import sys

import pytest

from strata import Variable, ConfigSpec, ConfigException, MissingValue
from strata.layers import CLILayer, EnvVarLayer, KwargLayer


class ApiKey(Variable):
    env_var_name = 'STRATA_TEST_API_KEY'


class Region(Variable):
    env_var_name = 'STRATA_TEST_REGION'
    default_value = 'us-west'


class Verbosity(Variable):
    is_cli_arg = True  # long arg name derived from Variable.name
    cli_action = 'count'
    default_value = 0


class Mode(Variable):
    cli_arg_name = 'mode'
    cli_short_arg_name = 'm'
    cli_const = 'fast'
    default_value = 'slow'


def test_env_var_layer(monkeypatch):
    Config = ConfigSpec([ApiKey, Region], [EnvVarLayer]).make_config()

    monkeypatch.setenv('STRATA_TEST_API_KEY', 'sekrit')
    monkeypatch.delenv('STRATA_TEST_REGION', raising=False)
    conf = Config()
    assert conf.api_key == 'sekrit'
    assert conf.region == 'us-west'  # unset env var falls through to default

    monkeypatch.setenv('STRATA_TEST_REGION', 'eu-central')
    assert Config().region == 'eu-central'

    monkeypatch.delenv('STRATA_TEST_API_KEY')
    with pytest.raises(ConfigException) as exc_info:
        Config()
    assert 'api_key' in str(exc_info.value)
    assert 'STRATA_TEST_API_KEY' in str(exc_info.value)


def test_env_var_layer_unset_raises_missing_value(monkeypatch):
    monkeypatch.delenv('STRATA_TEST_API_KEY', raising=False)
    provider = EnvVarLayer._get_provider(ApiKey)

    with pytest.raises(MissingValue) as exc_info:
        provider.func()
    assert 'STRATA_TEST_API_KEY' in str(exc_info.value)



def test_cli_layer_is_cli_arg_and_count(monkeypatch):
    Config = ConfigSpec([Verbosity, Mode], [KwargLayer, CLILayer]).make_config()

    monkeypatch.setattr(sys, 'argv', ['prog', '--verbosity', '--verbosity', '-m'])
    conf = Config()
    assert conf.verbosity == 2
    assert conf.mode == 'fast'
    assert '--verbosity' in conf.cli_help
    assert '-m' in conf.cli_help

    monkeypatch.setattr(sys, 'argv', ['prog'])
    conf = Config()
    assert conf.verbosity == 0
    assert conf.mode == 'slow'


def test_cli_layer_kwarg_precedence(monkeypatch):
    class Port(Variable):
        cli_arg_name = 'port'
        is_config_kwarg = True

    Config = ConfigSpec([Port], [KwargLayer, CLILayer]).make_config()
    monkeypatch.setattr(sys, 'argv', ['prog', '--port', '80'])
    assert Config().port == '80'
    assert Config(port=8080).port == 8080


def test_cli_layer_rejects_unknown_action(monkeypatch):
    class Weird(Variable):
        cli_arg_name = 'weird'
        cli_action = 'explode'

    Config = ConfigSpec([Weird], [CLILayer]).make_config()
    monkeypatch.setattr(sys, 'argv', ['prog'])
    with pytest.raises(ConfigException) as exc_info:
        Config()
    # the argparser provider fails, so nothing downstream can be provided
    assert 'unrecognized CLI action' in str(exc_info.value)
