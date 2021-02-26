#!/usr/bin/env python
# encoding: utf-8
#
# Copyright SAS Institute
#
#  Licensed under the Apache License, Version 2.0 (the License);
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

''' Install the SAS Optimization Modeling for Python (sasoptpy) '''

from setuptools import setup

__version__ = None
with open('./sasoptpy/version.py') as f:
    exec(f.read())

long_desc = '''
sasoptpy: SAS Optimization Interface for Python

- Repository: https://github.com/sassoftware/sasoptpy
- Issues: https://github.com/sassoftware/sasoptpy/issues
- Releases: https://github.com/sassoftware/sasoptpy/releases
- Community: https://communities.sas.com/t5/Mathematical-Optimization/bd-p/operations_research

Copyright (C) SAS Institute Inc.
'''

setup(
    name='sasoptpy',
    version=__version__,
    packages=['sasoptpy'],
    description='sasoptpy: SAS Optimization Interface for Python',
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url='https://github.com/sassoftware/sasoptpy',
    author='Sertalp B. Cay (SAS Institute)',
    author_email='Sertalp.Cay@sas.com',
    license='Apache v2.0',
    install_requires=[
        'pandas == 1.1.0',
        'swat == 1.6.1',
        'saspy == 3.3.7',
        'numpy == 1.15.4'
        ],
    setup_requires=[
        'numpy'
        ],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Mathematics"
    ],
    include_package_data=True,
)
