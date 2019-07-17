proc optmodel;
num N init 1000;
var x {{1..N}} >= 1 <= 2;
min f2 = sum {o10 in 1..N-1} (cos(- 0.5 * x[o10 + 1] - (x[o10]) ^ (2)));
solve with nlp / algorithm=activeset;
print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
print _con_.name _con_.body _con_.dual;
print x;
quit;