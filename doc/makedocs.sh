rm generated/*
make clean
make html
grep -r -l 'CASUSERHDFS' _build/html | xargs -r -d'\n' sed -i 's/CASUSERHDFS\(([A-Za-z0-9]*)\)/CASUSERHDFS(casuser)/g'
make latex
sed -i -- 's/CASUSERHDFS([A-Za-z0-9]*)/CASUSERHDFS(casuser)/g' _build/latex/sasoptpy.tex 
cd _build/latex
make
