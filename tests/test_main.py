import pytest
from argparse import Namespace
import os

from PIL.Image import Image

from dot2bgraph.main import _parse_args, _output_locations, main
from dot2bgraph.locations import Locations

# Prevent spinners from printing during tests
import dot2bgraph.utils.spinner
dot2bgraph.utils.spinner._SPINNER_DISABLE = True

@pytest.fixture
def locs():
    locs = Locations()
    locs.add_block()
    return locs

def test_args_empty(capsys):
    with pytest.raises(SystemExit):
        _parse_args([])

    captured = capsys.readouterr()
    assert captured.err
    assert not captured.out

def test_args_help(capsys):
    with pytest.raises(SystemExit):
        _parse_args(['-h'])

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out

def test_args_default():
    args = _parse_args(['in.dot'])

    assert args.dotfile == 'in.dot'
    assert args.format == 'json'
    assert args.output is None
    assert args.recursive == False

def test_args_json():
    args = _parse_args(['in.dot','-f','json'])

    assert args.dotfile == 'in.dot'
    assert args.format == 'json'
    assert args.output is None
    assert args.recursive == False

def test_args_output():
    args = _parse_args(['in.dot','-f','json','-o','out.json'])

    assert args.dotfile == 'in.dot'
    assert args.format == 'json'
    assert args.output == 'out.json'
    assert args.recursive == False

def test_args_png_output_recursive():
    args = _parse_args(['in','--format','png','--output','out.png','-R'])

    assert args.dotfile == 'in'
    assert args.format == 'png'
    assert args.output == 'out.png'
    assert args.recursive == True

def test_args_none():
    args = _parse_args(['in','--format','none','--recursive'])

    assert args.dotfile == 'in'
    assert args.format == 'none'
    assert args.output is None
    assert args.recursive == True

def test_args_invalid_format(capsys):
    with pytest.raises(SystemExit):
        _parse_args(['in.dot','-f','abc'])

    captured = capsys.readouterr()
    assert captured.err
    assert not captured.out

def test_args_invalid_no_dotfile(capsys):
    with pytest.raises(SystemExit):
        _parse_args(['-f','json'])

    captured = capsys.readouterr()
    assert captured.err
    assert not captured.out

def test_output_locations_json_stdout(locs, capsys):
    _output_locations(Namespace(
        format = 'json',
        output = None,
    ), locs)

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out

def test_output_locations_json_file(locs, capsys, tmp_path):
    out = tmp_path / 'test.json'

    _output_locations(Namespace(
        format = 'json',
        output = str(out),
    ), locs)

    captured = capsys.readouterr()
    assert not captured.err
    assert not captured.out

    assert open(out).readlines()

def test_output_locations_png_stdout(locs, capsys, monkeypatch):
    def mock_image_show(*args):
        print('abc')
    monkeypatch.setattr(Image, "show", mock_image_show)

    _output_locations(Namespace(
        format = 'png',
        output = None,
    ), locs)

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out

def test_output_locations_png_file(locs, capsys, tmp_path):
    out = tmp_path / 'test.png'

    _output_locations(Namespace(
        format = 'png',
        output = str(out),
    ), locs)

    captured = capsys.readouterr()
    assert not captured.err
    assert not captured.out

    assert open(out, 'rb').read()

def test_main_file(capsys, tmp_path):
    dotfile = tmp_path / 'test.dot'
    dotfile.write_text('digraph X { }')

    main([str(dotfile)])

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out

def test_main_dir(capsys, tmp_path):
    dir = tmp_path / 'dir'
    os.mkdir(dir)

    ex = dir / 'ex.dot'
    ex.write_text('digraph G { }')

    main([str(dir),'-R'])

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out
