# Publishing specdrive

Distribution name: **specdrive** (PyPI). Import / command name: **specflow**.

## Before first publish

- [ ] Add a `LICENSE` file and re-add `license`/classifier to `pyproject.toml`.
- [ ] Add a GitHub repo and `[project.urls]` to `pyproject.toml`.
- [ ] Bump `SCHEMA_VERSION` in `src/specflow/state.py` if releasing a new version
      (it is the single source of truth; the package version derives from it).
- [ ] `pytest` is green.

## Build and check

```sh
pip install -e ".[dev]" build twine
python -m build
twine check dist/*
```

Confirm `playbook.md` ships inside the wheel (adapters and `specflow playbook`
depend on it):

```sh
python -m zipfile -l dist/specdrive-*.whl | grep playbook.md
```

## Upload

Test on TestPyPI first:

```sh
twine upload --repository testpypi dist/*
pipx install --index-url https://test.pypi.org/simple/ specdrive
```

Then the real index:

```sh
twine upload dist/*
```
