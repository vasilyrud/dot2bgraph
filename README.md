# dot2bgraph

## Dev

```
pipenv shell
pipenv install --dev
```

### CLI

```
python -m dot2bgraph <dotfile>
```

### Pytest

```
python -m pytest -s --cov-report term-missing --cov=dot2bgraph
```

### Mypy

```
python -m mypy -p dot2bgraph --config-file=mypy.ini
```

### Profiling

```
PYTHONPATH=dot2bgraph python -mcProfile -o dot2bgraph.prof dot2bgraph/__main__.py -f none -R ~/Desktop/dots
```
