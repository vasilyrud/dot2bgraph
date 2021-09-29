# dot2bgraph

## Install

First, ensure that you have `graphviz` installed, since it is a dependency for `pygraphviz` which, in turn, is a dependency for `dot2bgraph`.

For example, in Ubuntu:

```
apt-get install graphviz graphviz-dev
```

Or in OSX:

```
brew install graphviz
```

For other platforms, see pygraphviz's [INSTALL.txt](https://github.com/pygraphviz/pygraphviz/blob/main/INSTALL.txt)

Then, install `dot2bgraph`:

```
pip install dot2bgraph
```

## Dev

```
mkdir .venv
pipenv shell
pipenv install --dev -e .
pipenv install -r requirements-dev.txt
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
