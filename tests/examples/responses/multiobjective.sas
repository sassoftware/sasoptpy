proc optmodel;
var x {{1,2}} >= 0 <= 5;
min f1 = (x[1] - 1) ^ (2) + (x[1] - x[2]) ^ (2);
min f2 = (x[1] - x[2]) ^ (2) + (x[2] - 3) ^ (2);
solve with lso obj (f1 f2) / logfreq=50;
quit;