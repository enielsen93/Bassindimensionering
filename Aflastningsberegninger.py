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
import os
import sys
i = 0
import copy
import rainreader

km2 = rainreader.KM2(
        r"C:\Users\ELNN\OneDrive - Ramboll\Documents\Aarhus Vand\Kongelund og Marselistunnel\MIKE\02_RAIN\Viby_godkendte_1979_2018.txt",
        initial_loss = 0.6, concentration_time = 7)
gaugetime = km2.gaugetime
gaugeint = km2.gaugeint
# Udløbstal

for catchment_area in [3.45e4, 2.95e4, 2.45e4, 1.95e4, 1e4]:

    # catchment_area = 0.95e4 # Bef. ha
    safety_factor = 1
    discharge = catchment_area/1e4*4.5/1e3 # m3/s


    # Initialiser volumen-matrix
    V = np.empty(len(gaugetime))

    # DT (Tidsafstand mellem to maks-værdier
    DT = 10

    inlet_discharge = catchment_area * gaugeint / 1e6 * safety_factor # Indloesvandfoering m3/s
    gaugetime_dt = np.diff(gaugetime) * 24 * 60 * 60# Beregner tidsskridt mellem hver vaerdi i regnmåler [s]

    # Initialiser Vmax (matrix for maksimal vandstand)
    #Vmax = np.empty((len(RP), len(udlobstal)))

    V_overflow = 50*catchment_area/1e4 # m3

    # Start volumen for bassin
    V[(0)] = 0 # Volumen til t = 0 er V = 0

    # Beregn potentiel udloebsvandfoering
    outlet_discharge_potential = discharge * gaugetime_dt # m3

    overflow = np.zeros(len(gaugetime))
    # Iterer over alle regnnedbør
    for i, t in enumerate(gaugetime[1:], start = 1):
        # Hvis volumen er over 0, er der vandføring i udløb
        if V[(i-1)] > V_overflow:
            overflow[i] = V[(i-1)] - V_overflow
            V[(i-1)] = V_overflow
        if V[(i - 1)] > 0:
            # Udløb er udløbstal -- Kan ikke overstige bassinvolumen
            # mm [l/s/ha -> mm/min]
            outlet_discharge = min(outlet_discharge_potential[i-1], V[(i - 1)])
        else:
            # Hvis volumen er lig 0, er der ingen udløb
            outlet_discharge = 0
        # Regn bassinvolumen til tiden t, ved V(t) = V(t-1) + ind - ud
        V[(i)] = V[(i - 1)] + inlet_discharge[i-1] * 60 - outlet_discharge

    print(u"Overløb %d m3 (1979-2018)" % (np.sum(overflow)))
    print(u"Overløb %d m3/år" % (np.sum(overflow)/38))
    # plt.figure()
    # plt.step(gaugetime, V)
    # plt.show()