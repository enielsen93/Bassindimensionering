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
functionsPath = [r"K:\Hydrauliske modeller\Makroer & Beregningsark\Functions", r"C:\Dokumenter\Makroer\Functions", os.path.join(os.path.dirname(os.path.dirname(__file__)),"Functions")]
i = 0
while not os.path.exists(functionsPath[i]):
    i += 1
sys.path.append(functionsPath[i])
import rainreader
import copy

[gaugetime, gaugeint] = rainreader.readKM2(
        r"K:\Hydrauliske modeller\Regn\Valg af Regn 2018\SilkeborgVandvaerk.km2", 
        initial_loss = 0.6, concentration_time = 0)

concentration_times = [0 ,7, 10, 14, 30, 55]#[0, 7, 10, 14, 30, 60, 100]

# Gentagelsesperiode
RP = ((gaugetime[-1]-gaugetime[0])/365.25)/np.arange(1,10)

# fig1 = plt.figure()
# ax1 = plt.subplot()

# fig2 = plt.figure()
# ax2 = plt.subplot(sharex = ax1)

# Udløbstal
catchment_area = 1.5 # Bef. ha
safety_factor = 1.35
infiltration_area = 400
infiltration_rate = 40 # mm/h
discharge = infiltration_area * (infiltration_rate/1e3/60/60*1e3)

# Initialiser volumen-matrix
V = np.empty(len(gaugetime))

# DT (Tidsafstand mellem to maks-værdier
DT = 10

inlet_discharge = catchment_area * gaugeint * safety_factor / 1e3 * 60 # Indløbsvandføring
gaugetime_dt = np.diff(gaugetime) * 24 * 60 # Beregner tidsskridt mellem hver værdi i regnmåler

# Initialiser Vmax (matrix for maksimal vandstand)
#Vmax = np.empty((len(RP), len(udlobstal)))

V_overflow = 550/(catchment_area*1e4)*1000#depth * infiltration_area / (catchment_area*1e4)*1e3

# Start volumen for bassin
V[(0)] = 0 # Volumen til t = 0 er V = 0

# Beregn potentiel udløbsvandføring
outlet_discharge_potential = discharge / 1e4 * 60 * gaugetime_dt

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
    V[(i)] = V[(i - 1)] + inlet_discharge[i-1] - outlet_discharge


time_series_duration = ((gaugetime[-1]-gaugetime[0])/365.25)
overflow_events_count = np.sum(np.diff(gaugetime[np.where(np.logical_and(overflow[1:] > 0, overflow[:-1] == 0))[0]])<1)+1
print("Gentagelsesperiode %1.2f" % (time_series_duration/overflow_events_count))
        

plt.close("all")
plt.figure()
plt.step(gaugetime, overflow)
plt.figure()
plt.step(gaugetime, V)

print("%1.2f%s af nedbøren går i overløb" % (np.sum(overflow)/np.sum(inlet_discharge)*1e2, r"%"))

road_width = 11 # m
road_length = catchment_area*1e4 / road_width 
infiltration_width = 1.5
infiltration_length = infiltration_area/infiltration_width
#print("%d m vej skal have %d meter vejbed" % (road_length, infiltration_length))

fig1,ax1 = plt.subplots(figsize = (6.69, 5))
plt.step(gaugetime, gaugeint / 1e3 *60 * safety_factor)
plt.step(gaugetime[:-2], overflow[2:])

fig2,ax2 = plt.subplots(figsize = (6.69, 5))
fig3,ax3 = plt.subplots(figsize = (6.69, 5))
fig4,ax4 = plt.subplots(figsize = (6.69, 5))
dts =[7, 10, 20, 30, 60, 120, 240]

RPi = 3
rain_depth_aggregated_baseline, j = rainreader.rainStatistics(gaugetime, gaugeint*safety_factor, dts)
idx = np.flipud(np.argsort(rain_depth_aggregated_baseline, axis=0))
rain_depth_aggregated_baseline_sorted = np.flipud(np.sort(rainreader.rainStatistics(gaugetime, gaugeint*safety_factor, dts)[0],axis=0))
ax2.plot(dts, rain_depth_aggregated_baseline_sorted [RPi,:-1],'.--', label = "Baseline")

# for share in [20, 35, 50]:
#     rain_depth_aggregated, j = readKM2.rainStatistics(gaugetime, 
#                                      gaugeint*(100-share)/1e2*1.65 + overflow*1e3/60 *(share)/1e2, dts)
#     idx2 = np.flipud(np.argsort(rain_depth_aggregated, axis=0))
#     rain_depth_aggregated_sorted = np.flipud(np.sort(rain_depth_aggregated, axis=0))
#     # rain_depth_aggregated = rain_depth_aggregated[idx2]
#     ax2.plot(dts, rain_depth_aggregated_sorted[RPi,:-1], '.--', label = "%d%s vejvand" % (share,r"%"))
    
rain_depth_aggregated, j = rainreader.rainStatistics(gaugetime, 
                                 gaugeint*1.65 + overflow*1e3/60, dts)
idx2 = np.flipud(np.argsort(rain_depth_aggregated, axis=0))
rain_depth_aggregated_sorted = np.flipud(np.sort(rain_depth_aggregated, axis=0))
# rain_depth_aggregated = rain_depth_aggregated[idx2]
ax2.plot(dts, rain_depth_aggregated_sorted[RPi,:-1], '.--')#, label = "%d%s vejvand" % (share,r"%"))

ax3.step(gaugetime, gaugeint*safety_factor)
ax3.step(gaugetime, overflow*1e3/60)

ax4.step(gaugetime, gaugeint*safety_factor + overflow*1e3/60)
ax4.step(gaugetime, gaugeint*safety_factor)

DTi = 0
#ax3.set_xlim([gaugetime[j[idx[RPi,DTi]]], gaugetime[j[idx[RPi,DTi]]]+1])
fig2.legend()
ax2.set_xlim([0, max(dts)])
ax2.set_ylim([0, ax2.get_ylim()[-1]])
ax2.grid(True)


# RDAgg_overflow = readKM2.rainStatistics(gaugetime, overflow, [7, 10, 20, 30, 60])
# RDAgg_overflow = np.flipud(np.sort(RDAgg_overflow,axis=0))
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
