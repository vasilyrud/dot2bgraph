# Copyright 2019 Vasily Rudchenko - bgraph
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

from blockgraph.locations import dot2locations

def main():

    parser = argparse.ArgumentParser(
        description='bgraph: large graph visualization')

    parser.add_argument('dotfile',
        help='Path to dot file.')

    args = parser.parse_args()

    with open(args.dotfile, 'r') as f:
        dot = ''.join(f.readlines())
        graph = dot2locations(dot)
