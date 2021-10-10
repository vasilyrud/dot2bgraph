# Copyright 2021 Vasily Rudchenko - dot2bgraph
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

import pathlib
from setuptools import setup, find_packages

NAME = 'dot2bgraph'
VERSION = '0.1.0'
URL = 'https://github.com/vasilyrud/dot2bgraph'

SHORT_DESCRIPTION = '''
A CLI to convert dot files to bgraph format for visualization.
'''.strip()

README = (pathlib.Path(__file__).parent / 'README.md').read_text()

DEPENDENCIES = [
    'pygraphviz',
    'rectpack',
    'Pillow',
    'tqdm',
    'yaspin',
]


setup(
    name=NAME,
    version=VERSION,
    url=URL,
    description=SHORT_DESCRIPTION,
    long_description=README,
    long_description_content_type='text/markdown',

    author='Vasily Rudchenko',
    author_email='vasily.rudchenko.dev@gmail.com',
    license='Apache Software License',

    python_requires='>=3.9',
    install_requires=DEPENDENCIES,

    entry_points={
        'console_scripts': [NAME + ' = dot2bgraph.main:main'],
    },

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',

        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: Information Analysis',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],

    keywords=[
        'graph',
        'visualization',
        'dot',
        'bgraph',
        'command',
        'line',
        'interface',
        'cli',
        'tool',
        'convert',
    ],

    packages=find_packages(),
    include_package_data=True,
)
