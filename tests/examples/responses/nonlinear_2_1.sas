proc optmodel;
num N init 1000;
var x {{1..N}} >= 1 <= 2;
min f2 = sum {i in 1..N-1} (cos(- 0.5 * x[i + 1] - (x[i]) ^ (2)));
solve with nlp / algorithm=activeset;
print x;
quit;