proc optmodel;
var x {{1,2}} >= 0 <= 5;
min f1 = (x[1] - 1) ^ (2) + (x[1] - x[2]) ^ (2);
min f2 = (x[1] - x[2]) ^ (2) + (x[2] - 3) ^ (2);
solve with lso obj (f1 f2) / logfreq=50;
print _var_.name _var_.lb _var_.ub _var_ _var_.rc;
print _con_.name _con_.body _con_.dual;
quit;