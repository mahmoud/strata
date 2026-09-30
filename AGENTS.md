# Agent Environment Notes

## Project overview

**strata** is a Python library (3.10+, no services, no database) that
resolves application configuration from layered sources: `Variable` classes
declare what is needed, `Layer` classes provide values (kwargs, CLI, env,
TOML file, defaults) in precedence order, and a `ConfigSpec` checks the
dependency graph at import time. Single package `strata/`, tests inside it at
`strata/tests/`, one runtime dependency (`boltons`; `tomli` on 3.10).

Compatibility surface: everything in `strata/__init__.py.__all__`, plus the
Variable hints table in [ARCHITECTURE.md](ARCHITECTURE.md). Versioning is
CalVer `YY.MINOR.MICRO` (first release `26.0.0`); the string lives only in
`strata/__init__.py`.

## Commands

All from the repo root. `uvx --with tox-uv tox` is the canonical runner (no
`tox` binary needed; `uv` fetches interpreters).

| Task | Command | Notes |
|------|---------|-------|
| Run tests (release evidence) | `uvx --with tox-uv tox -e py314` | Installs the package into `.tox/py314` and tests *that*; add `py310` for the `tomli` branch |
| Coverage floor | `uvx --with tox-uv tox -e py314,coverage-report` | Fails under `fail_under` in `pyproject.toml`; always run both envs together |
| Lint | `uvx --with tox-uv tox -e lint` | `ruff check strata`; config in `pyproject.toml` |
| Dev environment | `uv sync` | Creates `.venv` from `uv.lock` |
| Fast test loop | `uv run pytest strata/tests -x -q -k <name>` | Source tree, not the installed package |
| Build | `uv build` | Wheel + sdist into `dist/` |
| Release | `/skill:release` | See `.omp/skills/release/SKILL.md` |

## Operating loop

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) (5 minutes; it is the code map).
2. `uvx --with tox-uv tox -e py314,lint` before changing anything.
3. Make the change. New Layer or hint: test + hints-table row.
4. Same command again, plus `-e py314,coverage-report` if you touched `strata/`.
5. User-visible change: bullet under the top `## X.Y.Zdev`-less section of
   `CHANGELOG.md` (add a new `## <next version>` section if none is open).
6. Commit with a descriptive message. Do not push tags.

## Rules

### Never

- **Never edit `uv.lock` by hand.** `uv lock` regenerates it; the `Lockfile`
  CI job runs `uv sync --locked`.
- **Never cite a source-tree `pytest` run as release evidence.** Only the tox
  envs test the installed artifact (`tox.ini` `changedir = .tox`).
- **Never commit `.env`** (gitignored; holds agent keys).
- **Never change `__version__` outside the release skill.** The publish
  workflow refuses `dev` versions and tag/version mismatches.
- **Never hand-edit action SHAs in `.github/workflows/`.** Dependabot owns
  them (`.github/dependabot.yml`), one grouped PR a month.
- **Never lower `fail_under` or add coverage `omit`s to make a run pass.**
  Add tests for the uncovered lines instead.

### Always

- **Always raise `MissingValue` (fallthrough) or `LayerError` (fatal) from
  Layer providers**, never a bare exception, so `config._provider_results`
  stays legible.
- **Always add a test for a new Layer, hint, or validator** in
  `strata/tests/`, and a row in the ARCHITECTURE.md hints table.
- **Always run tests through tox before claiming they pass on the
  package.**
- **GoodTurn code references**: when an applied fix came from the GoodTurn
  commons, leave `# GoodTurn: https://goodturn.ai/p/<id>` on the line it
  lands, so the next reader can signal the outcome.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md): bird's-eye view, code map,
invariants, Variable hints, and how to add a Layer.

## Documentation

| File | Contents |
|------|----------|
| `ARCHITECTURE.md` | Code map and invariants |
| `CHANGELOG.md` | User-facing history; CalVer sections |
| `docs/dependencies.md` | Why `boltons` and `tomli`, and the policy for adding more |
| `docs/releasing.md` | Human release procedure, workflow chain, recovery table |
| `docs/roadmap.md` | Planned Layers and features, with the 2013 notes folded in |
| `.omp/skills/release/SKILL.md` | Executable release procedure (`/skill:release`) |
| `.github/workflows/tests.yml` | CI matrix: 3.10 to 3.14 Linux, 3.14 Windows/macOS, lint, coverage, package, lockfile |
| `.github/workflows/publish.yml` | Tag-triggered build, trusted publish to PyPI, verify from PyPI |

## Conventions

- Python: 4-space, single quotes, `%`-formatting is fine (ruff `UP031`
  ignored), line length 100. No type annotations required.
- Tests: plain pytest functions; `pytest.raises`; `tmp_path` and
  `monkeypatch` for files, env vars, and `sys.argv`. No mocks.
- Docs use ISO dates; changelog dates look like `_(September 30, 2026)_`.
