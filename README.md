# dot2bgraph

## Dev

```
pipenv shell
pipenv install --dev
```

### CLI

```
PYTHONPATH=dot2bgraph python dot2bgraph <dotfile>
```

### Pytest

```
PYTHONPATH=dot2bgraph python -m pytest -s --cov-report term-missing --cov=dot2bgraph
```

### Mypy

```
MYPYPATH=dot2bgraph mypy dot2bgraph --config-file=mypy.ini
```
