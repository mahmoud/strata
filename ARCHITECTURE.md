# strata Architecture

Code map in the [matklad ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)
sense: where things live, the invariants that hold them together, and how to
change them. Read this before touching `strata/`.

## Bird's-eye view

strata resolves application configuration at startup. Three concepts:

- **Variable**: a named value the application needs (`ServerPort`, `SecretKey`).
  A class; its attributes are *hints* that tell Layers how to find it.
- **Layer**: one source of values (constructor kwargs, CLI, environment, TOML
  file, in-code defaults). A Layer offers a **Provider** per Variable it can
  serve; a provider is a callable whose positional parameter names are the
  Variables it depends on.
- **ConfigSpec**: a list of Variables plus an ordered list of Layers. At
  construction it checks, once, that every Variable has at least one Provider
  and that the dependency graph is acyclic, then `make_config()` returns a
  `Config` class.

`Config(**kwargs)` runs a **ConfigProcessor**: a worklist over providers in
layer order. The first Layer whose provider returns a value wins; a provider
that raises is recorded as `Unsatisfied` and the next Layer gets its turn;
providers that never got a turn are `Pruned`. Every outcome is kept on
`config._provider_results`, so "why is `server_port` 5000?" is answerable.

Design rationale (from the original 2013 notes): configuration complexity
grows faster than application complexity because the interface is flat while
the sources are many (CLI, dotfile, env, defaults, generated). strata
decomposes that along three dimensions: Variables (what), Layers (from where),
and environments (which Layers, in which order; a dev spec adds a defaults
Layer, a prod spec omits it). It builds on argparse and friends rather than
replacing them, and targets in-process startup configuration, not deployment
or config management.

## Code map

| Module | Owns |
|--------|------|
| `strata/__init__.py` | The public API (`__all__`) and **the version string** (`__version__`). Nothing else defines either. |
| `strata/core.py` | `VariableMeta`/`Variable` (name derivation, `description`/`summary`), `Layer` (default `_get_provider`: a method named after the Variable; `_get_autoprovided`), `Provider` (the Layer x Variable intersection; `dep_names`; `get_bound`), `autoprovide` decorator and `ez_vars` (internal helpers, not in `__all__`). |
| `strata/config.py` | `ConfigSpec` (`var_provider_map`, `var_consumer_map`, `slot_order`, cycle/unresolved checks via `jit_toposort`), `ConfigProcessor` (worklist; `Satisfied`/`Unsatisfied`/`Pruned` results; `to_table()`), `BaseConfig` (what `make_config()` subclasses). |
| `strata/layers.py` | Built-in Layers: `KwargLayer`, `EnvVarLayer`, `CLILayer`, `TOMLFileLayer` (+ `ConfigFilePath` Variable), and the sandwich `StrataConfigLayer` (provides `config`) / `StrataDefaultLayer` (`default_value`). |
| `strata/validators.py` | `Validator` callables for `Variable.validator`: `Integer`, `Float`, `Boolean`, `Choice`, `List`, `FilePath`. Applied to the winning value; a validation error propagates (it is not a fallthrough). |
| `strata/errors.py` | Spec-time `ConfigSpecException` (`DependencyCycle`, `UnresolvedDependency`) vs run-time `ConfigException` (`MissingValue`, `LayerError`, `ProviderError`, `NotProvidable`). |
| `strata/utils.py` | `get_arg_names` / `inject`: `inspect.signature`-based dependency discovery and keyword injection. |
| `strata/tests/` | pytest suite, shipped in the wheel and run against the *installed* package by tox. |

## Invariants

- **Variable names** are `boltons.strutils.camel2under(ClassName)` unless the
  class sets `name`; never start with `_`. Subclassing a Variable yields a
  *new* name unless `name` is set explicitly (see `ConfigFilePath`).
- **Provider dependencies are positional parameter names.** A Layer method
  `def host_url(self, server_host, server_port)` depends on `server_host` and
  `server_port`. `self` is stripped for functions defined on the Layer class
  (`Provider._is_unbound_method`); `get_bound` rebinds with `types.MethodType`.
- **Layer order is precedence**, everywhere. `ConfigSpec.layers` is
  `[StrataConfigLayer] + yours + [StrataDefaultLayer]`. The processor's
  worklist keeps that order even for Variables pulled in as dependencies.
- **Fallthrough vs fatal.** Any exception from a provider (including
  `MissingValue`) means "this Layer can't; try the next". `LayerError` is the
  one exception that aborts instead; raise it for problems no lower Layer can
  fix (malformed config file). Validator errors also propagate.
- **Required = input Variables.** Autoprovided Variables (`cli_help`,
  `toml_config_data`) are attempted but their absence is not an error;
  every Variable passed to `ConfigSpec` must resolve or `ConfigException`
  lists each one with every Layer's reason.
- **Spec-time vs run-time.** Missing providers and cycles fail when the
  `ConfigSpec` is built (import time), never at `Config()` time.
- **Tests run against the installed package.** `tox.ini` sets
  `changedir = .tox` and points pytest at `{env_site_packages_dir}/strata/tests/`;
  a passing local `pytest strata/tests` is not release evidence.

## Variable hints read by built-in Layers

| Hint | Layer | Meaning |
|------|-------|---------|
| `is_config_kwarg = True` | `KwargLayer` | value comes from `Config(name=...)` |
| `cli_arg_name` / `cli_short_arg_name` | `CLILayer` | `--name` / `-n` (either or both) |
| `is_cli_arg = True` | `CLILayer` | `--<Variable.name>` |
| `cli_action` (`store`, `append`, `count`), `cli_const` | `CLILayer` | argparse action; `cli_const` turns it into `<action>_const` |
| `env_var_name` | `EnvVarLayer` | `os.environ[env_var_name]` |
| `config_key` (`'server.port'`) | `TOMLFileLayer` | dotted path into the TOML document |
| `is_config_key = True` | `TOMLFileLayer` | top-level key `Variable.name` |
| `default_value` | `StrataDefaultLayer` | last resort; also what makes a Variable optional in practice |
| `validator` | (all) | callable applied to the winning value |
| `description` / `summary` | (all) | docstring by default; `summary` feeds `--help` |

## How to change things

- **Add a Layer.** Subclass `Layer`; override `_get_provider(cls, var)` to
  read your hint and return `Provider(cls, var.name, callable)`, or raise
  `NotProvidable(cls, var, why)` at spec time. Inside the callable raise
  `MissingValue` for "not here, try the next Layer" and `LayerError` for
  "stop". Shared plumbing (a parsed file, an argparser) is a method listed in
  `_autoprovided` that your per-Variable callables depend on by name.
  `TOMLFileLayer` is the template. Add a row to the hints table above and a
  test in `strata/tests/test_layers.py` (or its own file).
- **Add a hint** to a built-in Layer: read it in `_get_provider` /
  the autoprovided method, document it in the table, test it.
- **Change resolution semantics** (`ConfigProcessor.process`): the tests in
  `strata/tests/test_processor.py` pin layer ordering, fallthrough on
  exhausted dependencies, and result recording. Update them deliberately.
- **Change the public API**: edit `strata/__init__.py.__all__`, add a
  `CHANGELOG.md` bullet.
