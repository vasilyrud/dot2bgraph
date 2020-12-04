import pytest

from colour import Color
from PIL import Image

from blockgraph.locations import Locations
from blockgraph.image import _color2rgb, _generate_pixels, locations2image

def test_color2rgb():
    assert _color2rgb(Color('#000000')) == (0,0,0)
    assert _color2rgb(Color('#cccccc')) == (204,204,204)
    assert _color2rgb(Color('#ffffff')) == (255,255,255)

def test_generate_pixels_empty():
    locs = Locations()
    expected_dim = (4, 4)

    pixels, dimension = _generate_pixels(locs)
    assert dimension == expected_dim
    assert len(pixels) == expected_dim[0] * expected_dim[1]
    assert all(pixel == (255,255,255) for pixel in pixels)

def test_generate_pixels():
    locs = Locations()
    locs.add_block(x=0, y=0, color="#cccccc")
    locs.add_edge_end(x=0, y=1)
    expected_dim = (5, 6)

    pixels, dimension = _generate_pixels(locs)
    assert dimension == expected_dim
    assert len(pixels) == expected_dim[0] * expected_dim[1]
    assert pixels[12] == (204,204,204)
    assert pixels[17] == (0,0,0)

def test_locations2image():
    locs = Locations()
    img = locations2image(locs)
    assert isinstance(img, Image.Image)
