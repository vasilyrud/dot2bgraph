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

from pathlib import Path

import sys
import argparse
import json

from dot2bgraph.utils.spinner import sp, SPINNER_OK
from dot2bgraph.converter.directed import dot2locations, dots2locations
from dot2bgraph.image import locations2image

def _output_locations(args, locations):
    if args.format == 'json':
        locations_obj = locations.to_obj()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(locations_obj, f)
        else:
            print(json.dumps(locations_obj, indent=4))

    elif args.format == 'png':
        image = locations2image(locations)

        if args.output:
            image.save(args.output)
        else:
            image.show()

def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description='dot2bgraph - a CLI to convert dot files to bgraph format for visualization.')

    parser.add_argument('dotfile',
        help='Path to dot file input.')
    parser.add_argument('-f', '--format', choices=['json', 'png', 'none'], default='json',
        help='Format of the output.')
    parser.add_argument('-o', '--output',
        help='Output file to save to.')
    parser.add_argument('-R', '--recursive', action='store_true',
        help='Look for dot files recursively and make directory structure part of the graph.')

    return parser.parse_args(argv)

def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    path = Path(args.dotfile)
    if args.recursive:
        locations = dots2locations(path)
    else:
        locations = dot2locations(path)

    with sp(type='spinner') as spinner:
        spinner.text='Generating output'
        _output_locations(args, locations)
        spinner.ok(SPINNER_OK)
