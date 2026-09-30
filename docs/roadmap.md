# Roadmap

Unordered. Each item is scoped so an agent can pick it up from
[ARCHITECTURE.md](../ARCHITECTURE.md) alone. Items marked *(2013)* come from
the original `NOTES.rst` / `strata/TODO.md`, folded in here when those files
were removed in 26.0.0.

## Layers

- **face-based `CLILayer`.** Today's `CLILayer` builds an `argparse` parser
  from hints. A `FaceCLILayer` (optional extra on
  [face](https://github.com/mahmoud/face)) would give subcommands, flag
  files, and `--help` that groups by Layer. Keep the argparse one; users
  without face need nothing new.
- **`ProtectedLayer` on pocket_protector.** Provide Variables whose hint is
  `protected_name = 'db_password'` from a `protected.yaml`, with the key
  passphrase itself a Variable (`env_var_name`). Optional extra.
- **Value references inside TOML.** FinFam/GoodTurn/pictomon config loaders
  resolve string values of the form `env:VAR:default` and
  `protected:<secret>` inside the TOML document. As a strata feature this is
  a post-processor on `TOMLFileLayer` values (or a wrapping Layer), not a
  change to the key lookup.
- **Flag-file layer.** A file whose presence toggles a boolean Variable
  (`/etc/app/maintenance`). Trivial Layer; useful as a documentation example.
- **Feature flags in the dependency graph** *(2013)*. Collect flags first,
  then drop disabled subgraphs from the worklist ("provide `NullConfig`s for
  end deps"). Concern recorded then: shared Variables can't be removed
  outright, only references to them.

## Introspection

- **`ConfigSpec.describe()`**: JSON export of every Variable (name, summary,
  hints, validator), every Layer, every Provider and its `dep_names`, and,
  given a `Config` instance, each Provider's result. "openapi.json for
  configuration": drives generated docs, a `--config-help` flag, and a web
  view of "why is this value what it is". `ConfigProcessor.to_table()` is
  the seed.
- **Automatic listing of what each Layer provides** *(2013)*: covered by
  `describe()`.

## Variables

- **`_specialize(prefix)` namespacing** *(2013)*. One ConfigSpec per
  component, composed under prefixes (`db.host`, `cache.host`). Was a no-op
  stub; removed in 26.0.0. Design question still open: whether Variables
  must be unique across specs.
- **Uniqueness check** *(2013)*: reject duplicate Variable names when a
  `ConfigSpec` is built (today the later one silently wins in
  `name_var_map`).
- **Instantiated Variables** *(2013)*: `process_value` instantiates the
  Variable class per value today (`_var = _var()`); decide whether Variables
  are types or instances and settle `validator` vs `process_value`.
- **Default values** *(2013)*: `default_value` is a hint on the Variable
  today; consider a `get_default()` hook or a `default_factory`.

## Validators *(2013, still relevant)*

Most are post-processors, not just validators:

- Quantity: one-or-none, one-or-more, zero-or-more, exactly N.
- File-based: is file/dir/symlink, readable/writable (`FilePath` has
  `should_exist` and `min_perms` only).
- `URL`, `LocalPort` are empty classes; implement or delete.
- `Boolean(strict=False)` accepted strings: `true/yes/on/1`, `false/no/off/0`.

## Processing

- **Eager provides** *(2013)*: run a provider as soon as its dependencies
  are available rather than in worklist order. Only matters if dependencies
  are added or removed during fulfillment ("dynamic depends"), which nothing
  does yet.
- **Validation failure policy** *(2013)*: today a validator error propagates
  out of `Config()`. Alternative: treat it like a provider failure and fall
  through. Decide, document in ARCHITECTURE.md invariants, test.
- **Global state** *(2013)*: `ConfigSpec` is the unit; nothing is global.
  Keep it that way; revisit only with `_specialize`.
