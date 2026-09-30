# strata Changelog

Versions follow [CalVer](https://calver.org) (`YY.MINOR.MICRO`).

## 26.0.0

_(September 30, 2026)_

First release. strata was a Python 2 prototype from 2013; this release
ports it to Python 3.10 through 3.14 and ships it on PyPI.

- Python 3.10, 3.11, 3.12, 3.13, and 3.14 support; Python 2 dropped.
  Providers are introspected with `inspect.signature`, so any callable
  with positional parameters works as a provider.
- New `TOMLFileLayer` and `ConfigFilePath` Variable: read Variables
  from a TOML file via `config_key = 'server.port'` (dotted path) or
  `is_config_key = True` (top-level key named after the Variable).
  Missing file or key falls through to lower layers; a malformed file
  raises the new `LayerError`, which aborts processing instead of
  falling through.
- Depends on [boltons](https://github.com/mahmoud/boltons) for
  `Table`, `FilePerms`, `camel2under`/`under2camel`, and
  `make_sentinel`; the vendored `tableutils` and `fileutils` modules
  are gone.
- `ConfigProcessor` resolves dependencies in layer order. Previously
  a Variable pulled in as another provider's dependency could be
  satisfied by a lower layer before a higher one ran, and the
  required-variable worklist started in `set` (hash) order.
- A provider whose dependency no layer could provide is now
  `Unsatisfied` and the next layer gets its turn, instead of aborting
  the whole Config. Unresolved Variables still raise
  `ConfigException`, now listing every layer's reason.
- `CLILayer`: `is_cli_arg = True` without `cli_arg_name` works
  (previously `AttributeError`); an unknown `cli_action` raises
  `ValueError`.
- `validators.Boolean`, `Choice`, and `List` actually validate
  (they were stubs).
- `strata` exports `ConfigSpecException`, `LayerError`,
  `MissingValue`, `NotProvidable`, `TOMLFileLayer`, `ConfigFilePath`.
- Removed dead code: `BaseLayer`, `FileValue`, `toposort`,
  `Layer._specialize`, `ConfigSpec.from_modules`.
- Packaging: `pyproject.toml` (flit), `tox` + `uv`, GitHub Actions
  test matrix (3.10 to 3.14 on Linux, 3.14 on Windows and macOS),
  ruff lint, coverage floor, and tag-triggered trusted publishing to
  PyPI.
