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

import argparse
import json
import sys

from blockgraph.converter.directed import dot2locations
from blockgraph.image import locations2image

def output_locations(args, locations):
    if args.format == 'json':
        locations_obj = locations.to_obj()
        print(json.dumps(locations_obj, indent=4))

    elif args.format == 'png':
        image = locations2image(locations)
        image.show()

    else:
        print('Invalid output format specified.')
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='bgraph: large graph visualization')

    parser.add_argument('dotfile',
        help='Path to dot file input.')
    parser.add_argument('--format', choices=['json', 'png'], default='json',
        help='Format of the output.')

    args = parser.parse_args()

    with open(args.dotfile, 'r') as f:
        dot = ''.join(f.readlines())

    locations = dot2locations(dot)
    output_locations(args, locations)
