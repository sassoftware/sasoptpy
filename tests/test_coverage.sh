#!/bin/bash
set -e
cd ..
coverage run --source sasoptpy -m unittest discover -s tests/ -p 'test*.py'
coverage html
coverage report -m
