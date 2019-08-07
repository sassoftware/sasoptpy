proc optmodel;
num N init 1000;
var x {{1..N}} init 1;
min f = sum {i in 1..N-1} (- 4 * x[i] + 3) + sum {i in 1..N-1} (((x[i]) ^ (2) + (x[N]) ^ (2)) ^ (2));
solve with nlp / ;
print x;
quit;