# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 11:09:58 2018

@author: Eniel
"""
import numpy as np  # matrix manipulation

import datetime  # time series management
from datetime import datetime as dtnow  # get time of code
import matplotlib.dates as dates  # time series management
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import rainreader

km2 = rainreader.KM2(
        r"\\files\Projects\RWA2022N000XX\RWA2022N00009\_Modtaget_modeller\Regnserier\Viby_godkendte_1979_2018.txt", 
        initial_loss = 0.6, concentration_time = 30)

gaugetime, gaugeint = km2.gaugetime, km2.gaugeint

# Gentagelsesperiode
RP = ((gaugetime[-1]-gaugetime[0])/365.25)/np.arange(1,10)

udlobstal = [50, 60, 70, 80, 100, 125, 150]
#udlobstal = [0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2, 3, 4, 6, 8, 12, 20]

# Udløbstal
catchment_area = 6.54 # Bef. ha
sikkerhedsfaktor = 1.00

# Initialiser volumen-matrix
V = np.zeros((len(gaugetime), len(udlobstal)))

# DT (Tidsafstand mellem to maks-værdier
DT = 10

inlet_discharge = catchment_area * gaugeint / 1e3 * 60 * sikkerhedsfaktor # Indløbsvandføring
gaugetime_dt = np.diff(gaugetime) * 24 * 60 # Beregner tidsskridt mellem hver værdi i regnmåler
Vmax = np.empty((100, len(udlobstal)))

for udlobidx in range(len(udlobstal)): # Kører løkke for alle udløbstal
    # Beregn potentiel udløbsvandføring
    outlet_discharge_potential = gaugetime_dt * udlobstal[udlobidx] / 1e4 * 60  
    
    overflow = np.zeros(len(gaugetime))
    # Iterer over alle regnnedbør
    for i, t in enumerate(gaugetime[1:], start = 1):
        # Hvis volumen er over 0, er der vandføring i udløb
        if V[(i - 1, udlobidx)] > 0:
            # Udløb er udløbstal -- Kan ikke overstige bassinvolumen
            # mm [l/s/ha -> mm/min]
            outlet_discharge = min(outlet_discharge_potential[i-1], V[(i - 1, udlobidx)])
        else:
            # Hvis volumen er lig 0, er der ingen udløb
            outlet_discharge = 0
        # Regn bassinvolumen til tiden t, ved V(t) = V(t-1) + ind - ud
        V[(i, udlobidx)] = V[(i - 1, udlobidx)] + inlet_discharge[i-1] - outlet_discharge
    
    idx = np.flip(np.argsort(V[:, udlobidx]), axis=0)
    Vmax[0, udlobidx] = V[(idx[0], udlobidx)]

    # Find de maksimale bassinvolumener til det gældende udløbstal
    # To volumener skal være sepereret med en t = DT, før de inkluderes
    idx = np.flip(np.argsort(V[:, udlobidx]), axis=0)
    tmax = [gaugetime[idx[0]]]
    Vmax[0, udlobidx] = V[(idx[0], udlobidx)]
    k = 1
    for i in range(len(gaugetime)):
        if np.min(([abs(tmax - gaugetime[idx[i]])])) > DT:
            Vmax[k, udlobidx] = V[idx[i], udlobidx]
            tmax.append(gaugetime[idx[i]])
            k += 1
        # Hvis 100 hændelser fundet, stop
        if k == 100:
            break

for udlobi in range(len(udlobstal)):
    print("%d: %d" % (udlobstal[udlobi], np.interp(5, (38/np.array(range(1,len(Vmax[:,udlobi])+1)))[::-1],Vmax[::-1,udlobi])*10))