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

from tqdm import tqdm
from yaspin import yaspin

SPINNER_OK = '✔'
_SPINNER_DISABLE = False

class NoSpinner:
    ''' Class used to "hide" a Yaspin spinner when
    _SPINNER_DISABLE is set.
    '''
    def __init__(self, *args, **kwargs):
        self.text = ''
    def __enter__(self, *args, **kwargs):
        return self
    def __exit__(self, *args, **kwargs):
        pass
    def ok(self, *args, **kwargs):
        pass
    def fail(self, *args, **kwargs):
        pass

def sp(*args, **kwargs):
    sp_type = kwargs.pop('type', 'spinner')

    if sp_type == 'bar':
        return tqdm(
            kwargs['items'],
            desc=kwargs.pop('text', ''), 
            bar_format='{desc} {n_fmt} out of {total_fmt} |{bar}|',
            disable=_SPINNER_DISABLE,
        )

    elif sp_type == 'spinner':
        if _SPINNER_DISABLE:
            return NoSpinner()
        return yaspin(*args, **kwargs)

    assert False, 'Invalid spinner type'
