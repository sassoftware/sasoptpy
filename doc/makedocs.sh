#!/bin/bash

echo 'Building documentation... use "no-ex" argument to disable experiments'

# Parse options
export clean_f='true'
if [ $# -gt 0 ]; then
if [ $1 == 'no-ex' ]; then echo 'disabled experiments...'; export ignore='ex'; fi
fi
if [ $# -gt 1 ]; then
if [ $2 == 'no-api' ]; then echo 'disabled API...'; export ignore_api='true'; fi
fi
if [ $# -gt 2 ]; then
if [ $3 == 'no-clean' ]; then echo 'will skip cleaning...'; export clean_f='false'; fi
fi

# Optional cleaning
if [ "$clean_f" != "false" ]; then
rm api/generated/*
rm savefig/*
make clean
fi

# Generate html
make html
# Replace sensitive information
grep -r -l 'CASUSERHDFS' _build/html | xargs -r -d'\n' sed -i 's/CASUSERHDFS\(([A-Za-z0-9]*)\)/CASUSERHDFS(casuser)/g'
# Make pdf
make latex
sed -i -- 's/CASUSERHDFS([A-Za-z0-9]*)/CASUSERHDFS(casuser)/g' _build/latex/sasoptpy.tex 
cd _build/latex
make
cp sasoptpy.pdf ../html

# Cleaning
unset ignore
unset ignore_api
unset clean_f
