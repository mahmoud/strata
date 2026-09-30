# strata

Multi-dimensional, topologically-driven, dependency-resolving
configuration framework, built to handle the complexities of advanced
projects.

strata separates *what* an application needs configured (`Variable`
classes) from *where* values come from (`Layer` classes: constructor
kwargs, CLI arguments, environment variables, TOML files, in-code
defaults). A `ConfigSpec` joins a list of Variables with an ordered
list of Layers, checks at import time that every Variable has at least
one provider and that no dependency cycles exist, and produces a
`Config` class. Instantiating it resolves every Variable: the first
Layer that can produce a value wins, layer methods can depend on other
Variables by naming them as parameters, and every provider's outcome
(satisfied, unsatisfied, pruned) is recorded for inspection.

## Install

```
pip install strata
```

Python 3.10+. Depends on [boltons](https://github.com/mahmoud/boltons)
(and `tomli` on 3.10).

## Usage

```python
from strata import (Variable, Layer, ConfigSpec, ConfigFilePath,
                    KwargLayer, CLILayer, EnvVarLayer, TOMLFileLayer)


class ServerHost(Variable):
    cli_arg_name = 'host'
    is_config_kwarg = True
    config_key = 'server.host'


class ServerPort(Variable):
    cli_arg_name = 'port'
    is_config_kwarg = True
    config_key = 'server.port'


class SecretKey(Variable):
    env_var_name = 'APP_SECRET_KEY'


class HostURL(Variable):
    "Full URL of the server, derived from host and port."


class DevDefaultLayer(Layer):
    def server_host(self):
        return '127.0.0.1'

    def server_port(self):
        return 5000

    def secret_key(self):
        return 'dev-only-secret'

    def host_url(self, server_host, server_port):  # depends on two Variables
        return f'http://{server_host}:{server_port}/'


VAR_LIST = [ServerHost, ServerPort, SecretKey, HostURL, ConfigFilePath]
spec = ConfigSpec(VAR_LIST, [KwargLayer, CLILayer, EnvVarLayer,
                             TOMLFileLayer, DevDefaultLayer])
Config = spec.make_config()

config = Config(config_file_path='app.toml')
config.server_port  # kwarg, else --port, else [server] port in app.toml, else 5000
config.host_url     # 'http://127.0.0.1:5000/'
```

Drop `DevDefaultLayer` from the list to get a production spec that
refuses to start without real values: instantiation raises
`ConfigException` naming each unresolved Variable and every Layer's
reason for not providing it.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the resolution model and
the Variable hints each built-in Layer reads.

## License

BSD 3-clause, see [LICENSE](LICENSE).
