# dot2bgraph

## Dev

```
pipenv shell
pipenv install --dev
```

### CLI

```
python dot2bgraph <dotfile>
```

### Pytest

```
PYTHONPATH=dot2bgraph python -m pytest -s --cov-report term-missing --cov=dot2bgraph/blockgraph
```

### Mypy

```
python -m mypy -p dot2bgraph --config-file=mypy.ini
```

### Profiling

```
PYTHONPATH=dot2bgraph python -mcProfile -o dot2bgraph.prof dot2bgraph/__main__.py -f none -R ~/Desktop/dots
```
