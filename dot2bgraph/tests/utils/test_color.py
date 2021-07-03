import pytest
from colour import Color

from blockgraph.utils.color import bgraph_color

def test_bgraph_color():
    assert bgraph_color(Color('#000000')) == 0
    assert bgraph_color(Color('#ff0000')) == 16711680
    assert bgraph_color(Color('#0000ff')) == 255
    assert bgraph_color(Color('#00ff00')) == 65280
    assert bgraph_color(Color('#ffffff')) == 16777215
