import pytest

from dot2bgraph.utils.color import bgraph_color

def test_bgraph_color():
    assert bgraph_color((  0,  0,  0)) == 0
    assert bgraph_color((255,  0,  0)) == 16711680
    assert bgraph_color((  0,  0,255)) == 255
    assert bgraph_color((  0,255,  0)) == 65280
    assert bgraph_color((255,255,255)) == 16777215
