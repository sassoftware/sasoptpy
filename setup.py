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

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='sasoptpy',
    version='0.2.1',
    packages=['sasoptpy'],
    description='sasoptpy: SAS Optimization Interface for Python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/sassoftware/sasoptpy',
    author='Sertalp B. Cay (SAS Institute)',
    author_email='Sertalp.Cay@sas.com',
    license='Apache v2.0',
    install_requires=[
        'pandas >= 0.23.3',
        'swat >= 1.4.0',
        'numpy >= 1.14.5',
        'flask >= 1.0.2',
        'flask_restful >= 0.3.6',
        'itsdangerous >= 0.24',
        'gevent >= 1.4.0'
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
