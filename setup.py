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

setup(
    name='sasoptpy',
    version='0.2.1.dev0',
    packages=['sasoptpy'],
    description='sasoptpy: SAS Optimization Interface for Python',
    url='https://github.com/sassoftware/sasoptpy',
    author='Sertalp B. Cay (SAS Institute)',
    author_email='Sertalp.Cay@sas.com',
    license='Apache v2.0',
    install_requires=[
        'pandas >= 0.16.0',
        'swat >= 1.2.0.dist',
        'numpy'
        ],
    setup_requires=[
        'numpy'
        ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Mathematics"
    ),
)
