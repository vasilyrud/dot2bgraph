# dot2bgraph [![Travis (.com)](https://img.shields.io/travis/com/vasilyrud/dot2bgraph)](https://travis-ci.com/github/vasilyrud/dot2bgraph)

`dot2bgraph` is a CLI utility to convert graphs in `dot` format to `bgraph` format, for visualization with tools like [bgrapher](https://github.com/vasilyrud/bgrapher).

`dot2bgraph` supports a subset of `dot` features, tailored specifically to those that convert neatly to `bgraph` format. Other `dot` attributes that do not correlate to attributes supported by `bgraph` (e.g., shapes, label positions, etc.) are ignored.

## Installation

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

## Usage

By default an input "file.dot" is converted to `bgraph` JSON format, which is outputted to stdout:

```
dot2bgraph file.dot
```

If you instead wish to quickly look at the output as it would appear in a `bgraph` visualization tool, use `-f png`, i.e., "PNG format". For example:

```
dot2bgraph -f png file.dot
```

For creating a bgraph recursively from multiple dot files in a directory structure, use `-R`, e.g. for the following directory structure:

```
dotdir
├── file1.dot
└── subdotdir
    └── file2.dot
```

You can run:

```
dot2bgraph -R dotdir
```

To save the tool's output (in whichever format) to a file, use `-o`.

## Development

### Install

```
mkdir .venv
pipenv shell
pipenv install --dev -e .
pipenv install -r requirements-dev.txt
```

### Test

#### Pytest

```
python -m pytest -s --cov-report term-missing --cov=dot2bgraph
```

#### Mypy

```
python -m mypy -p dot2bgraph --config-file=mypy.ini
```

#### Profile

```
python -mcProfile -o dot2bgraph.prof dot2bgraph/__main__.py -f none <your_dot_file>
```
