import pytest

from strata import Variable, ConfigSpec, ConfigException, ConfigFilePath, LayerError
from strata.layers import KwargLayer, TOMLFileLayer, tomllib


class ServerPort(Variable):
    config_key = 'server.port'
    is_config_kwarg = True


class ServerHost(Variable):
    is_config_key = False
    default_value = '127.0.0.1'


class Debug(Variable):
    is_config_key = True
    default_value = False


class DatabaseURL(Variable):
    config_key = 'db.url'  # no default: must come from the file


VARS = [ServerPort, ServerHost, Debug]


def _make_config(tmp_path, variables=VARS, text=None, filename='app.toml'):
    path = tmp_path / filename
    if text is not None:
        path.write_text(text)

    class AppConfigFilePath(ConfigFilePath):
        name = 'config_file_path'
        default_value = str(path)

    spec = ConfigSpec(variables + [AppConfigFilePath], [KwargLayer, TOMLFileLayer])
    return spec.make_config()


def test_toml_values_and_default_fallthrough(tmp_path):
    Config = _make_config(tmp_path, text='[server]\nport = 8080\nhost = "0.0.0.0"\n')
    conf = Config()
    assert conf.server_port == 8080
    assert conf.debug is False  # key missing in file, falls through to default
    assert conf.server_host == '127.0.0.1'  # is_config_key=False: file ignored
    assert conf.toml_config_data == {'server': {'port': 8080, 'host': '0.0.0.0'}}


def test_toml_top_level_key(tmp_path):
    Config = _make_config(tmp_path, text='debug = true\n[server]\nport = 1\n')
    assert Config().debug is True


def test_kwarg_layer_wins_over_toml(tmp_path):
    Config = _make_config(tmp_path, text='[server]\nport = 8080\n')
    assert Config(server_port=9000).server_port == 9000


def test_missing_file_falls_through(tmp_path):
    Config = _make_config(tmp_path, variables=[Debug], text=None)
    assert Config().debug is False


def test_missing_file_without_default_is_config_exception(tmp_path):
    Config = _make_config(tmp_path, variables=[DatabaseURL], text=None)
    with pytest.raises(ConfigException) as exc_info:
        Config()
    assert 'could not provide' in str(exc_info.value)
    assert 'config file not found' in str(exc_info.value)


def test_missing_key_without_default_is_config_exception(tmp_path):
    Config = _make_config(tmp_path, variables=[DatabaseURL], text='[db]\nname = "x"\n')
    with pytest.raises(ConfigException) as exc_info:
        Config()
    assert "no value at 'db.url'" in str(exc_info.value)


def test_malformed_toml_is_fatal(tmp_path):
    # every Variable here has a default, but a broken file must not
    # silently fall through to them
    Config = _make_config(tmp_path, variables=[Debug], text='[server\nport = = 1\n')
    with pytest.raises(LayerError) as exc_info:
        Config()
    assert 'invalid TOML' in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, tomllib.TOMLDecodeError)


def test_config_file_path_from_kwarg(tmp_path):
    (tmp_path / 'other.toml').write_text('[server]\nport = 4242\n')
    Config = _make_config(tmp_path, text='[server]\nport = 1\n')
    conf = Config(config_file_path=str(tmp_path / 'other.toml'))
    assert conf.server_port == 4242
