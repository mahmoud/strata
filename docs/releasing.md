# Releasing strata

strata uses [CalVer](https://calver.org/) (`YY.MINOR.MICRO`, e.g. `26.0.0`).
Tags are bare version numbers (`26.0.0`, not `v26.0.0`).

## Version lifecycle

During development `strata/__init__.py` carries a `dev` suffix:

```python
__version__ = '26.0.1dev'
```

At release time the suffix is removed, the commit is tagged, and the version
is bumped to the next `dev`. The publish workflow refuses to upload a version
containing `dev` or one that differs from the tag.

## Prerequisites (one-time, done 2026-09-30)

- **PyPI trusted publisher** on https://pypi.org/manage/project/strata/settings/publishing/:
  GitHub, owner `mahmoud`, repository `strata`, workflow `publish.yml`,
  environment `pypi`. No API tokens anywhere.
- **GitHub environment** `pypi` on the repo (no protection rules).

## Automated release

```
/skill:release
```

`.omp/skills/release/SKILL.md` walks through the steps below with pre-flight
checks and post-publish verification. The human retains one decision: the
skill stops before `git push origin master --tags`.

## Manual steps

1. Clean tree on `master`; tests green on the installed package:
   `uvx --with tox-uv tox -e py310,py314,lint`.
2. Strip `dev` from `__version__` in `strata/__init__.py`.
3. Add a `## X.Y.Z` / `_(Month D, YYYY)_` section at the top of `CHANGELOG.md`.
4. `git commit -am "strata version X.Y.Z"`
5. `git tag -a X.Y.Z -m "lowercase summary of the release"`
6. Bump to `X.Y.(Z+1)dev`; `git commit -am "bump version to X.Y.(Z+1)dev"`
7. `git push origin master --tags`
8. Verify from outside the repo:
   `uv venv /tmp/sv && uv pip install --python /tmp/sv/bin/python strata==X.Y.Z && (cd /tmp && /tmp/sv/bin/python -c "import strata; print(strata.__version__)")`

## What the push triggers

```
git push origin master --tags
  ├─ Tests (push to master): matrix, lint, coverage, package, lockfile
  └─ Publish to PyPI (tag X.Y.Z)
       build   -> validate __version__ == tag and no `dev`; uv build; upload dist/ artifact
       publish -> environment `pypi`, id-token: write, pypa/gh-action-pypi-publish
       verify  -> poll pypi.org JSON, install from PyPI in /tmp, check __version__, run tests
```

The artifact that reaches PyPI is the one `build` produced and CI inspected;
nothing is built on a laptop.

## Recovery

| Symptom | Cause | Fix |
|---------|-------|-----|
| `build` fails "contains dev suffix" / "does not match" | tagged the wrong commit | `git tag -d X.Y.Z && git push origin :refs/tags/X.Y.Z`, fix, re-tag |
| `publish` fails `invalid-publisher` | PyPI trusted publisher settings differ from the workflow | fix on PyPI, delete and re-push the tag |
| `verify` fails "Installed version ... does not match" | PyPI propagation slower than 5 min, or wrong artifact | re-run the job; if it persists, inspect the wheel on PyPI |
| tag on GitHub, nothing on PyPI | publish never ran or failed | PyPI is canonical: delete the tag, reset `__version__` to `X.Y.Zdev`, restart |
| version already on PyPI | cannot be re-uploaded | bump micro and release again |
