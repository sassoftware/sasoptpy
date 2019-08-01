proc optmodel;
num N init 1000;
var x {{1..N}} init 1;
min f = sum {o8 in 1..N-1} (- 4 * x[o8] + 3) + sum {o12 in 1..N-1} (((x[o12]) ^ (2) + (x[N]) ^ (2)) ^ (2));
solve with nlp / ;
print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
print _con_.name _con_.body _con_.dual;
print x;
quit;