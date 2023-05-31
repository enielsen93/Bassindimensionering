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
# while not os.path.exists(functionsPath[i]):
#     i += 1
import copy
import rainreader

km2 = rainreader.KM2(
        r"\\files\Projects\RWA2022N000XX\RWA2022N00009\_Modtaget_modeller\Regnserier\Viby_godkendte_1979_2018.txt",
        initial_loss=0.6, concentration_time= 20)
gaugetime, gaugeint = km2.gaugetime, km2.gaugeint


# Gentagelsesperiode
RP = 38

# fig1 = plt.figure()
# ax1 = plt.subplot()

# fig2 = plt.figure()
# ax2 = plt.subplot(sharex = ax1)

# Udløbstal
V_overflows = [250, 500, 750,  1000, 1500, 2000, 3000, 5000]
infiltration_areas = [250, 500, 750,  1000, 1500, 2000, 3000, 5000]

total_cleansed = np.empty((len(V_overflows), len(infiltration_areas)))

for V_overflow_i, V_overflow in enumerate(V_overflows):
    for infiltration_area_i, infiltration_area in enumerate(infiltration_areas):
        catchment_area = 27.87e4 # m2
        safety_factor = 1
        # infiltration_area = 1820 # m2
        # depth = 0.3 # m
        infiltration_rate = 5e-6 # m/s
        discharge = infiltration_area * infiltration_rate # m3/s

        # Initialiser volumen-matrix
        V = np.empty(len(gaugetime))

        # DT (Tidsafstand mellem to maks-værdier
        DT = 10

        inlet_discharge = catchment_area * gaugeint * 1e-6 * safety_factor # Indløbsvandføring
        gaugetime_dt = np.diff(gaugetime) * 24 * 60 * 60 # Beregner tidsskridt mellem hver værdi i regnmåler

        # Initialiser Vmax (matrix for maksimal vandstand)
        #Vmax = np.empty((len(RP), len(udlobstal)))

        # V_overflow = 1000

        # Start volumen for bassin
        V[(0)] = 0 # Volumen til t = 0 er V = 0

        # Beregn potentiel udløbsvandføring
        outlet_discharge_potential = discharge * gaugetime_dt

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
            V[(i)] = V[(i - 1)] + inlet_discharge[i-1]*60 - outlet_discharge

        total_cleansed[V_overflow_i, infiltration_area_i] = np.sum(overflow)/(np.sum(inlet_discharge)*60)*1e2

# print("Gentagelsesperiode %1.2f" % (((gaugetime[-1]-gaugetime[0])/365.25)/len(np.where(np.logical_and(overflow[1:] > 0, overflow[:-1] == 0))[0])))
#
#
# plt.close("all")
# plt.figure()
# plt.step(gaugetime, overflow)
# plt.figure()
# plt.step(gaugetime, V)
# plt.title("Volume")
#
# plt.figure()
# plt.step(gaugetime, inlet_discharge,'k')
# plt.step(gaugetime[1:], outlet_discharge_potential, 'r')
# plt.show()
#
        print(V_overflow, infiltration_area, np.sum(overflow)/(np.sum(inlet_discharge)*60)*1e2)

V_overflow = 948
infiltration_area = 1820
catchment_area = 27.87e4 # m2
safety_factor = 1
# infiltration_area = 1820 # m2
# depth = 0.3 # m
infiltration_rate = 5e-6 # m/s
discharge = infiltration_area * infiltration_rate # m3/s

# Initialiser volumen-matrix
V = np.empty(len(gaugetime))

# DT (Tidsafstand mellem to maks-værdier
DT = 10

inlet_discharge = catchment_area * gaugeint * 1e-6 * safety_factor # Indløbsvandføring
gaugetime_dt = np.diff(gaugetime) * 24 * 60 * 60 # Beregner tidsskridt mellem hver værdi i regnmåler

# Initialiser Vmax (matrix for maksimal vandstand)
#Vmax = np.empty((len(RP), len(udlobstal)))

# V_overflow = 1000

# Start volumen for bassin
V[(0)] = 0 # Volumen til t = 0 er V = 0

# Beregn potentiel udløbsvandføring
outlet_discharge_potential = discharge * gaugetime_dt

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
    V[(i)] = V[(i - 1)] + inlet_discharge[i-1]*60 - outlet_discharge

print(total_cleansed)

plt.subplots(figsize = (6.18, 5))
for i in range(len(V_overflows)):
    plt.plot(infiltration_areas, 100-total_cleansed[i,:],'k--', )
    plt.text(np.max(infiltration_areas)+50, 100-total_cleansed[i,-1], "%d" % V_overflows[i], horizontalalignment = "left", verticalalignment = 'center')

plt.text(plt.xlim()[1]+50, plt.ylim()[1], 'Volumen\n[$m^3$]')
plt.plot(infiltration_area, 100-np.sum(overflow)/(np.sum(inlet_discharge)*60)*1e2, 'ko')
plt.xlabel(r'Overfladeareal af bassin [$m^2$]')
plt.ylabel(r'Renset årsnedbør [$\%$]')
plt.show()
plt.grid()
plt.ylim([0, 100])
plt.xlim([0, 5000])
plt.subplots_adjust(right=0.87)
print(".")
#
# road_width = 11 # m
# road_length = catchment_area*1e4 / road_width
# infiltration_width = 1.5
# infiltration_length = infiltration_area/infiltration_width
# print("%d m vej skal have %d meter vejbed" % (road_length, infiltration_length))
## Find de maksimale bassinvolumener til det gældende udløbstal
## To volumener skal være sepereret med en t = DT, før de inkluderes
#idx = np.flip(np.argsort(V[:]), axis=0)
#tmax = [gaugetime[idx[0]]]
#Vmax[0, udlobidx] = V[(idx[0], udlobidx)]
#k = 1
#for i in range(len(gaugetime)):
#    if np.min(([abs(tmax - gaugetime[idx[i]])])) > DT:
#        Vmax[k, udlobidx] = V[idx[i], udlobidx]
#        tmax.append(gaugetime[idx[i]])
#        k += 1
#    # Hvis nok hændelser fundet, stop
#    if k == len(RP):
#        break
#    # ax1.step(gaugetime, V[:,udlobidx],'.--', label = concentration_time)
#    # ax2.step(gaugetime, gaugeint,'.--', label = concentration_time)
#
## Omregn de 100 maksimale hændelser iht. gentagelsesperiode
#TimeSeriesDuration = (gaugetime[-1]-gaugetime[0])/365.25 # Varighed af regnserie [år]
#VRP = np.empty((len(RP), len(Vmax[0, :])))
#for i in range(len(Vmax[0, :])):
#    for RPidx in range(len(RP)):
#        VRP[RPidx, i] = np.interp(RP[RPidx], np.sort(
#            [TimeSeriesDuration / float(1 + j) for j in range(len(Vmax[:, i]))]), np.sort(Vmax[:, i]))
#
