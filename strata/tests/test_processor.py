import pytest

from boltons.tableutils import Table

from strata import Variable, Layer, ConfigSpec, ConfigException
from strata.config import ConfigProcessor, Pruned, Satisfied, Unsatisfied
from strata.core import Provider
from strata.errors import ProviderError, NotProvidable
from strata.layers import KwargLayer


class Port(Variable):
    is_config_kwarg = True


class Host(Variable):
    pass


class Url(Variable):
    pass


class DefaultsLayer(Layer):
    def port(self):
        return 5000

    def host(self):
        return 'localhost'

    def url(self, host, port):
        return f'{host}:{port}'


LAYERS = [KwargLayer, DefaultsLayer]
Config = ConfigSpec([Port, Host, Url], LAYERS).make_config()


def _results_by_layer(config, var_name):
    return {res.by.layer_type.__name__: res
            for provider, res in config._provider_results.items()
            if provider.var_name == var_name}


def test_provider_results_record_winner_and_losers():
    conf = Config(port=8080)
    assert conf.url == 'localhost:8080'
    by_layer = _results_by_layer(conf, 'port')
    assert isinstance(by_layer['KwargLayer'], Satisfied)
    assert by_layer['KwargLayer'].value == 8080
    assert isinstance(by_layer['DefaultsLayer'], Pruned)
    assert by_layer['DefaultsLayer'].value == '<already satisfied>'

    conf = Config()
    by_layer = _results_by_layer(conf, 'port')
    assert isinstance(by_layer['KwargLayer'], Unsatisfied)
    assert isinstance(by_layer['KwargLayer'].value, KeyError)
    assert isinstance(by_layer['DefaultsLayer'], Satisfied)


def test_dependency_layer_order_is_respected():
    # 'url' pulls 'host'/'port' onto the worklist as dependencies; the
    # kwarg provider must still beat the default provider there
    class OnlyUrl(Variable):
        pass

    class UrlLayer(Layer):
        def only_url(self, host, port):
            return f'{host}:{port}'

    Config2 = ConfigSpec([OnlyUrl, Port, Host], [KwargLayer, UrlLayer, DefaultsLayer]).make_config()
    assert Config2(port=1).only_url == 'localhost:1'
    assert Config2().only_url == 'localhost:5000'


def test_failed_dependency_falls_through_to_next_layer():
    class Derived(Variable):
        pass

    class Needy(Variable):
        pass

    class FlakyLayer(Layer):
        _autoprovided = ['needy']

        def needy(self):
            raise RuntimeError('no needy today')

        def derived(self, needy):
            return 'from flaky'

    class FallbackLayer(Layer):
        def derived(self):
            return 'from fallback'

    # needy is an input variable: required, and nobody can provide it
    Config3 = ConfigSpec([Derived, Needy], [FlakyLayer, FallbackLayer]).make_config()
    with pytest.raises(ConfigException) as exc_info:
        Config3()
    msg = str(exc_info.value)
    assert "could not resolve: ['needy']" in msg
    assert 'no needy today' in msg

    # needy is only autoprovided: attempted, not required, so derived
    # falls through to FallbackLayer and the failure is recorded
    Config4 = ConfigSpec([Derived], [FlakyLayer, FallbackLayer]).make_config()
    conf = Config4()
    assert conf.derived == 'from fallback'
    assert not hasattr(conf, 'needy')
    flaky_res = _results_by_layer(conf, 'derived')['FlakyLayer']
    assert isinstance(flaky_res, Unsatisfied)
    assert 'no needy today' in str(flaky_res.value)


def test_to_table_and_repr():
    conf = Config(port=8080)
    table = conf._config_proc.to_table()
    assert isinstance(table, Table)
    # one row per layer, including the strata sandwich layers
    assert len(table) == len(conf._config_spec.layers)
    rendered = table.to_text()
    assert 'DefaultsLayer' in rendered
    assert '8080' in rendered
    assert repr(conf._config_proc).startswith('<ConfigProcessor:')
    assert repr(conf) == 'Config(port=8080)'


def test_debug_output(capsys):
    proc = ConfigProcessor(Config(port=1, _defer=True), debug=True)
    proc.process()
    out = capsys.readouterr().out
    assert 'Pruned' in out  # DefaultsLayer.port loses to the kwarg
    assert 'DefaultsLayer.port' in out


def test_provider_errors():
    with pytest.raises(ProviderError):
        Provider(DefaultsLayer, 'port', 42)  # not callable at all

    class BadLayer(Layer):
        port = 'not a method'

    with pytest.raises(NotProvidable) as exc_info:
        BadLayer._get_provider(Port)
    assert 'not callable' in str(exc_info.value)

    provider = DefaultsLayer._get_provider(Url)
    assert provider.dep_names == ('host', 'port')
    assert repr(provider) == 'Provider(DefaultsLayer.url(host, port))'
    with pytest.raises(TypeError):
        provider.get_bound(KwargLayer())
    bound = provider.get_bound(DefaultsLayer())
    assert bound.is_bound
    assert bound.dep_names == ('host', 'port')
