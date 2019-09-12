proc optmodel;
var static_production {{'coal','steel','transport'}} >= 0;
min Zero = 0;
con static_con_coal : 0.9 * static_production['coal'] - 0.5 * static_production['steel'] - 0.4 * static_production['transport'] = 60.0;
con static_con_steel : 0.9 * static_production['steel'] - 0.1 * static_production['coal'] - 0.2 * static_production['transport'] = 60.0;
con static_con_transport : 0.8 * static_production['transport'] - 0.2 * static_production['coal'] - 0.1 * static_production['steel'] = 30.0;
solve;
quit;