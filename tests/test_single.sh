#!/bin/bash

cd ..
coverage run --source sasoptpy -m unittest tests/${1} && coverage html
