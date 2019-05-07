#!/bin/bash
cd ..
coverage run --source sasoptpy -m unittest discover -s tests/ -p 'test*.py'
coverage html
#cd tests