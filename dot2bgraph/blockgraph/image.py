# Copyright 2020 Vasily Rudchenko - dot2bgraph
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from PIL import Image

PADDING = 2

def _generate_pixels(locs):
    img_width  = locs.width  + 2*PADDING
    img_height = locs.height + 2*PADDING

    depths = [[0 for j in range(img_width)] for i in range(img_height)]
    img    = [[(255,255,255) for j in range(img_width)] for i in range(img_height)]

    for block in locs.iter_blocks():
        for i in range(block.y, block.y + block.height):
            for j in range(block.x, block.x + block.width):
                y = i + PADDING
                x = j + PADDING

                if block.depth < depths[y][x]: continue

                img[y][x] = block.color
                depths[y][x] = block.depth

    for edge_end in locs.iter_edge_ends():
        y = edge_end.y + PADDING
        x = edge_end.x + PADDING

        img[y][x] = (0,0,0)

    return [pixel for row in img for pixel in row], (img_width, img_height)

def locations2image(locs):
    pixels, dimension = _generate_pixels(locs)

    image = Image.new('RGB', dimension)
    image.putdata(pixels)

    return image
