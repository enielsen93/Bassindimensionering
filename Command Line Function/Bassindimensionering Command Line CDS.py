# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 11:09:58 2018

@author: Eniel
"""
import numpy as np  # matrix manipulation
import pandas as pd

import datetime  # time series management
from datetime import datetime as dtnow  # get time of code
import matplotlib.dates as dates  # time series management
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import rainreader
import sys

if __name__ == "__main__":
    rainseries_file = sys.argv[1]
    catchment_area = float(sys.argv[2]) # bef. ha
    discharge = float(sys.argv[3]) # L/s
    sikkerhedsfaktor = float(sys.argv[4]) # -

    with open(rainseries_file, 'r') as f:
        txt = f.read()

    delimiter = r"  " if "  " in txt else r"\t"
    if "," in txt:
        txt = txt.replace(r",", r".")
        rainseries_file = StringIO(unicode(txt))

    series = pd.read_csv(rainseries_file, delimiter=delimiter, skiprows=3, names=["Intensity"], engine='python')
    series.index = pd.to_datetime(series.index)
    series = series.resample("60S").ffill()

    rain_event = np.concatenate((series.values[:, 0], np.zeros(60)))
    gaugetime, gaugeint = dates.date2num(series.index.to_pydatetime()), rain_event

    udlobstal = [discharge]
    #udlobstal = [0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2, 3, 4, 6, 8, 12, 20]

    # Udløbstal
    # catchment_area = 7.2 # Bef. ha
    # sikkerhedsfaktor = 1.00

    # Initialiser volumen-matrix
    V = np.zeros((len(gaugetime), len(udlobstal)))

    # DT (Tidsafstand mellem to maks-værdier
    DT = 10

    inlet_discharge = catchment_area * gaugeint / 1e3 * 60 * sikkerhedsfaktor # Indløbsvandføring
    gaugetime_dt = np.diff(gaugetime) * 24 * 60 # Beregner tidsskridt mellem hver værdi i regnmåler
    Vmax = np.empty((100, len(udlobstal)))
    for udlobidx in range(len(udlobstal)):
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

        idx = np.flipud(np.argsort(V[:, udlobidx]))
        Vmax[0, udlobidx] = V[(idx[0], udlobidx)]
    print("%d" % np.max(V*10))