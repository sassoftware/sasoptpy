proc optmodel;
   var x {{1,2}} >= 0 <= 5;
   min f1 = (x[1] - 1) ^ (2) + (x[1] - x[2]) ^ (2);
   min f2 = (x[1] - x[2]) ^ (2) + (x[2] - 3) ^ (2);
   solve with blackbox obj (f1 f2) / logfreq=50;
   create data allsols from [s]=(1.._NVAR_) name=_VAR_[s].name {j in 1.._NSOL_} <col('sol_'||j)=_VAR_[s].sol[j]>;
quit;