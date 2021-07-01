# Copyright 2020 Vasily Rudchenko - bgraph
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

from pathlib import Path

import argparse
import json

from blockgraph.converter.directed import dot2locations, dots2locations
from blockgraph.image import locations2image

def output_locations(args, locations):
    if args.format == 'json':
        locations_obj = locations.to_obj()
        print(json.dumps(locations_obj, indent=4))

    elif args.format == 'png':
        image = locations2image(locations)
        image.show()

def main():
    parser = argparse.ArgumentParser(
        description='bgraph: large graph visualization')

    parser.add_argument('dotfile',
        help='Path to dot file input.')
    parser.add_argument('-f', '--format', choices=['json', 'png', 'none'], default='json',
        help='Format of the output.')
    parser.add_argument('-R', '--recursive', action='store_true',
        help='Look for dot files recursively and make directory structure part of the graph.')

    args = parser.parse_args()

    path = Path(args.dotfile)
    if args.recursive:
        locations = dots2locations(path)
    else:
        locations = dot2locations(path)

    output_locations(args, locations)
