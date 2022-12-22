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
import matplotlib
import os
import sys
functionsPath = [r"K:\Hydrauliske modeller\Makroer & Beregningsark\Functions", r"C:\Dokumenter\Makroer\Functions", os.path.join(os.path.dirname(os.path.dirname(__file__)),"Functions")]
i = 0
while not os.path.exists(functionsPath[i]):
    i += 1
sys.path.append(functionsPath[i])
import rainreader

[gaugetime, gaugeint] = rainreader.readKM2(
        r"K:\Hydrauliske modeller\Regn\Valg af Regn 2021\SilkeborgVandvaerk.km2", 
        initial_loss = 0.6, concentration_time = 0)

# Gentagelsesperiode
RP = ((gaugetime[-1]-gaugetime[0])/365.25)/np.arange(1,10)

udlobstal = np.logspace(start = -0.5, stop = 8, num = 100, base = 2)
#udlobstal = [0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2, 3, 4, 6, 8, 12, 20]

# Udløbstal
catchment_area = 1 # Bef. ha
sikkerhedsfaktor = 1.35

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

# Omregn de 100 maksimale hændelser iht. gentagelsesperiode
TimeSeriesDuration = 43-1 # Varighed af regnserie [år]
RP = [1,5,10,20,40]
VRP = np.empty((len(RP), len(Vmax[0, :])))
for i in range(len(Vmax[0, :])):
    for RPidx in range(len(RP)):
        VRP[RPidx, i] = np.interp(RP[RPidx], np.sort(
            [TimeSeriesDuration / float(1 + j) for j in range(len(Vmax[:, i]))]), np.sort(Vmax[:, i]))

# Skriv årsmiddelnedbør ud
print("Årsmiddelnedbør = %1.0f" % (sum(gaugeint) / 1000 * 60 / 39.1))

VRPSaved = VRP

import win32clipboard as clipboard
def toClipboardForExcel(array):
    """
    Copies an array into a string format acceptable by Excel.
    Columns separated by \t, rows separated by \n
    """
    # Create string from array
    line_strings = []
    for line in array:
        line_strings.append("\t".join(line.astype(str)).replace("\n", ""))
    array_string = "\r\n".join(line_strings)

    # Put string into clipboard (open, clear, set, close)
    clipboard.OpenClipboard()
    clipboard.EmptyClipboard()
    clipboard.SetClipboardText(array_string)
    clipboard.CloseClipboard()


toClipboardForExcel(VRP)

# Laver figur
plt.close("all")
fig, ax = plt.subplots(figsize=(8.79, 6.69))
#fig, ax = plt.subplots(figsize=(6.69, 3.54))
#yOffset = [15,15,-40,30,10]
yOffset = [15,15,-40,30,10]

cutoff = 4
udlobstal2 = np.array(udlobstal)
udlobstal2 = np.concatenate((udlobstal2[udlobstal2<=cutoff], np.arange(1,np.sum(udlobstal2>cutoff)+1)+cutoff))

cmap = plt.get_cmap("Set1")
for i in range(len(RP)):
    plt.plot(udlobstal2,VRP[i,:]*10, color = cmap(i), linewidth = 2)#,linestyle = linestyles[linestylesSelect[i]])
    ax.text(8.2, VRP[i,-1]*10, u"%d år"  % (RP[i]), color = cmap(i), verticalalignment = "center", fontweight = 'semibold')
#    plt.text(10.1,VRP[i,udlobstal.index(10)]*10+yOffset[i],u"T = %1.0f år" % RP[i],verticalalignment='center')
    
#plt.xlim([0,11.8])
plt.ylim([0,2000])
plt.grid(b=True, which='major', color='#666666', linestyle='-',alpha=0.6)
plt.minorticks_on()
plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
plt.ylabel("Bassinvolumen [m$^3$/bef. ha]")
plt.xlabel(u"Afløbstal [L/sek./bef. ha]")
ax.yaxis.set_minor_locator(MultipleLocator(50))
ax.yaxis.set_major_locator(MultipleLocator(250))
plt.tight_layout()
matplotlib.pyplot.grid(True, which="both")

textstr = u"Regnmåler-station: 5192\nSilkeborg Vandværk (1979-2021)\nKlimafaktor = 1,35\nHydr. reduktionsfaktor = 1,0"

# these are matplotlib.patch.Patch properties
props = dict(boxstyle='round', facecolor='white', alpha=1)

# place a text box in upper left in axes coords
ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top',horizontalalignment='right', bbox=props)
#ax.set_xscale("log",base = 2)
## periode med fyldt bassin
#for i in np.where(gaugetime_dt>1.5)[0]:
#    print(V[i-1])

# place a text box in upper left in axes coords
ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top',horizontalalignment='right', bbox=props)
#ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
plt.xlim([0.0, 9])
ax.set_xticks([0, 0.5, 1, 2, 3, 4, 5,6,7,8])
ax.set_xticklabels([0, 0.5, 1, 2, 3, 4, 6,8,12,20])
plt.tight_layout()
## periode med fyldt bassin
#for i in np.where(gaugetime_dt>1.5)[0]:
#    print(V[i-1])