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
import readKM2

[gaugetime, gaugeint] = readKM2.readKM2(
        r"K:\Hydrauliske modeller\Regn\Valg af Regn 2021\SilkeborgVandvaerk.km2")

concentration_times = [0,7,10, 14, 30, 55]#[0, 7, 10, 14, 30, 60, 100]

# Gentagelsesperiode
RP = ((gaugetime[-1]-gaugetime[0])/365.25)/np.arange(1,10)

# fig1 = plt.figure()
# ax1 = plt.subplot()

# fig2 = plt.figure()
# ax2 = plt.subplot(sharex = ax1)

# Udløbstal
udlobstal = np.logspace(np.log2(0.25), np.log2(1000), num = 30, base = 2) # L/s/ha
VRP_conctime = np.zeros((len(concentration_times), len(RP), len(udlobstal)))

for concentration_time_i, concentration_time in enumerate(concentration_times):
    # Læs KM2-fil
    [gaugetime, gaugeint] = readKM2.readKM2(
        r"K:\Hydrauliske modeller\Regn\Valg af Regn 2021\SilkeborgVandvaerk.km2", 
        initial_loss = 0.0, concentration_time = concentration_time)
    
    # Initialiser volumen-matrix
    V = np.empty((len(gaugetime), len(udlobstal)))
    
    # DT (Tidsafstand mellem to maks-værdier
    DT = 10
    
    inlet_discharge = gaugeint / 1e3 * 60 # Indløbsvandføring
    gaugetime_dt = np.diff(gaugetime) * 24 * 60 # Beregner tidsskridt mellem hver værdi i regnmåler
    
    # Initialiser Vmax (matrix for maksimal vandstand)
    Vmax = np.empty((len(RP), len(udlobstal)))
    # Volumen, vandføring ind og ud af bassinet regnes alle i mm
    for udlobidx in range(len(udlobstal)): # Kører løkke for alle udløbstal
        print("%d/%d" % (udlobidx+1,len(udlobstal)))
        # Start volumen for bassin
        V[(0, udlobidx)] = 0 # Volumen til t = 0 er V = 0
        
        # Beregn potentiel udløbsvandføring
        outlet_discharge_potential = udlobstal[udlobidx] / 1e4 * 60 * gaugetime_dt
    
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
            # Hvis nok hændelser fundet, stop
            if k == len(RP):
                break
        # ax1.step(gaugetime, V[:,udlobidx],'.--', label = concentration_time)
        # ax2.step(gaugetime, gaugeint,'.--', label = concentration_time)
    
    # Omregn de 100 maksimale hændelser iht. gentagelsesperiode
    TimeSeriesDuration = (gaugetime[-1]-gaugetime[0])/365.25 # Varighed af regnserie [år]
    VRP = np.empty((len(RP), len(Vmax[0, :])))
    for i in range(len(Vmax[0, :])):
        for RPidx in range(len(RP)):
            VRP[RPidx, i] = np.interp(RP[RPidx], np.sort(
                [TimeSeriesDuration / float(1 + j) for j in range(len(Vmax[:, i]))]), np.sort(Vmax[:, i]))
    VRP_conctime[concentration_time_i,:,:] = VRP[:,:]
# # Skriv årsmiddelnedbør ud
# print("Årsmiddelnedbør = %1.0f" % (sum(gaugeint) / 1000 * 60 / 39.1))
# ax1.legend()
# ax2.legend()

plt.figure()
fig1, ax1 = plt.subplots(figsize=(6.69, 5))
for concentration_time_i, concentration_time in enumerate(concentration_times):
    plt.plot(udlobstal, np.mean([VRP_conctime[concentration_time_i, i, :]/VRP_conctime[0, i, :]*1e2 for i in range(4)],axis=0), '.--', label = "%d min" % concentration_time)
    # plt.plot(udlobstal, VRP_conctime[concentration_time_i, 4, :], label = concentration_time)
plt.legend(title = "Koncentrationstid")
ax1.set_xscale("log", base = 2)
ax1.set_ylabel("Reduktion i bassinvolumen ift. 0 min. koncentrationstid [%]")
ax1.set_xlim([0.03, 1000])
ax1.set_xticks([float(f'{float(f"{tick:.1g}"):g}') for tick in ax1.get_xticks()])
ax1.set_xticklabels([f'{float(f"{tick:.1g}"):g}' for tick in ax1.get_xticks()])
ax1.set_xlabel("Afløbstal [L/s/bef. ha]")


ax2 = ax1.twiny()
ax2.set_xscale("log", base = 2)
ax2.set_xbound(ax1.get_xbound())
ax2.set_xticks([float(f'{float(f"{tick:.1g}"):g}') for tick in ax1.get_xticks()])
ax2.set_xticklabels([f'{float(f"{tick*2:.1g}"):g}' for tick in ax1.get_xticks()])
ax1.set_ylim([0, 100])
ax1.grid()

# VRPSaved = VRP

# import win32clipboard as clipboard
# def toClipboardForExcel(array):
#     """
#     Copies an array into a string format acceptable by Excel.
#     Columns separated by \t, rows separated by \n
#     """
#     # Create string from array
#     line_strings = []
#     for line in array:
#         line_strings.append("\t".join(line.astype(str)).replace("\n", ""))
#     array_string = "\r\n".join(line_strings)

#     # Put string into clipboard (open, clear, set, close)
#     clipboard.OpenClipboard()
#     clipboard.EmptyClipboard()
#     clipboard.SetClipboardText(array_string)
#     clipboard.CloseClipboard()


# toClipboardForExcel(VRP)

# # Laver figur
# plt.close("all")
# #fig, ax = plt.subplots(figsize=(8.66, 6.69))
# fig, ax = plt.subplots(figsize=(6.69, 3.54))
# #yOffset = [15,15,-40,30,10]
# yOffset = [15,15,-40,30,10]

# cmap = plt.get_cmap("Set1")
# for i in range(len(RP)):
#     plt.plot(udlobstal[2:-2],VRP[i,2:-2]*10, color = cmap(i))#,linestyle = linestyles[linestylesSelect[i]])
#     plt.text(10.1,VRP[i,udlobstal.index(10)]*10+yOffset[i],u"T = %1.0f år" % RP[i],verticalalignment='center')
    
# plt.xlim([0,11.8])
# plt.ylim([0,1750])
# plt.grid(b=True, which='major', color='#666666', linestyle='-',alpha=0.6)
# plt.minorticks_on()
# plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
# plt.ylabel("Bassinvolumen [m$^3$/bef. ha]")
# plt.xticks(range(11))
# plt.xlabel(u"Afløbstal [L/sek./bef. ha]")
# ax.yaxis.set_minor_locator(MultipleLocator(50))
# ax.yaxis.set_major_locator(MultipleLocator(250))
# plt.tight_layout()

# textstr = u"Regnmåler-station: 5192\nSilkeborg Vandværk (1979-2017)\nKlimafaktor = 1,3\nHydr. reduktionsfaktor = 1,0"

# # these are matplotlib.patch.Patch properties
# props = dict(boxstyle='round', facecolor='white', alpha=0.5)

# # place a text box in upper left in axes coords
# ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
#         verticalalignment='top',horizontalalignment='right', bbox=props)



# #plt.savefig("Grafik\BassinkurverLille.png",dpi=600)