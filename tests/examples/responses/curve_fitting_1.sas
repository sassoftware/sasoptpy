proc optmodel;
set POINTS;
num x {POINTS};
num y {POINTS};
read data None into POINTS=[_N_] x y;
num order init 1;
var beta {{0..order}};
impvar estimate {o8 in POINTS} = beta[0] + sum {k in 1..order} (beta[k] * (x[o8]) ^ (k));
var surplus {{POINTS}} >= 0;
var slack {{POINTS}} >= 0;
con abs_dev_con {o29 in POINTS} : y[o29] - estimate[o29] + surplus[o29] - slack[o29] = 0;

var minmax;
con minmax_con {o39 in POINTS} : minmax - surplus[o39] - slack[o39] >= 0;

min Linfobj = minmax;
solve;
print x y estimate surplus slack;
quit;