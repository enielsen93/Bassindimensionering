# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 11:09:58 2018

@author: Eniel
"""
import numpy as np  # matrix manipulation
import re  # regex for reading KM2

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

def tic():
    # Homemade version of matlab tic and toc functions
    import time
    global startTime_for_tictoc
    startTime_for_tictoc = time.time()


def toc():
    import time
    if 'startTime_for_tictoc' in globals():
        print("Elapsed time is " + \
            str(time.time() - startTime_for_tictoc) + " seconds.")
    else:
        print("Toc: start time not set")

tic()

# Læs KM2-fil
[gaugetime, gaugeint] = rainreader.readKM2(
    r"K:\Hydrauliske modeller\Regn\Valg af Regn 2018\SilkeborgVandvaerk.km2", initial_loss = 0, concentration_time = 0)

# Gentagelsesperiode
RP = [1, 5, 10, 20, 40] # år
# Udløbstal
udlobstal = [1*2.5/1.35] # L/s/ha
# Initialiser volumen-matrix
V = np.empty((len(gaugetime), len(udlobstal)))
# DT (Tidsafstand mellem to maks-værdier
DT = 10

# Initialiser Vmax (matrix for maksimal vandstand)
Vmax = np.empty((100, len(udlobstal)))

# Volumen, vandføring ind og ud af bassinet regnes alle i mm
for udlobidx in range(len(udlobstal)): # Kører løkke for alle udløbstal
    print("%d/%d" % (udlobidx+1,len(udlobstal)))
    # Start volumen for bassin
    V[(0, udlobidx)] = 0 # Volumen til t = 0 er V = 0

    # Iterer over alle regnnedbør
    for i, t in enumerate(gaugetime):
        # Beregn tidsskridt
        dt = (gaugetime[i] - gaugetime[i - 1]) * 24 * 60  # min [d -> min]
        ind = gaugeint[i] / 1e3 * 60

        # Hvis volumen er over 0, er der vandføring i udløb
        if V[(i - 1, udlobidx)] > 0:
            # Udløb er udløbstal -- Kan ikke overstige bassinvolumen
            # mm [l/s/ha -> mm/min]
            ud = np.min([udlobstal[udlobidx] / 1e4 *
                         60 * dt, V[(i - 1, udlobidx)]])
        else:
            # Hvis volumen er lig 0, er der ingen udløb
            ud = 0
        # Regn bassinvolumen til tiden t, ved V(t) = V(t-1) + ind - ud
        V[(i, udlobidx)] = V[(i - 1, udlobidx)] + ind - ud

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


toc()
# Omregn de 100 maksimale hændelser iht. gentagelsesperiode
TimeSeriesDuration = 39.1 # Varighed af regnserie [år]
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
#fig, ax = plt.subplots(figsize=(8.66, 6.69))
fig, ax = plt.subplots(figsize=(6.69, 3.54))
#yOffset = [15,15,-40,30,10]
yOffset = [15,15,-40,30,10]

cmap = plt.get_cmap("Set1")
for i in range(len(RP)):
    plt.plot(udlobstal[2:-2],VRP[i,2:-2]*10, color = cmap(i))#,linestyle = linestyles[linestylesSelect[i]])
    plt.text(10.1,VRP[i,udlobstal.index(10)]*10+yOffset[i],u"T = %1.0f år" % RP[i],verticalalignment='center')
    
plt.xlim([0,11.8])
plt.ylim([0,1750])
plt.grid(b=True, which='major', color='#666666', linestyle='-',alpha=0.6)
plt.minorticks_on()
plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
plt.ylabel("Bassinvolumen [m$^3$/bef. ha]")
plt.xticks(range(11))
plt.xlabel(u"Afløbstal [L/sek./bef. ha]")
ax.yaxis.set_minor_locator(MultipleLocator(50))
ax.yaxis.set_major_locator(MultipleLocator(250))
plt.tight_layout()

textstr = u"Regnmåler-station: 5192\nSilkeborg Vandværk (1979-2017)\nKlimafaktor = 1,3\nHydr. reduktionsfaktor = 1,0"

# these are matplotlib.patch.Patch properties
props = dict(boxstyle='round', facecolor='white', alpha=0.5)

# place a text box in upper left in axes coords
ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top',horizontalalignment='right', bbox=props)



#plt.savefig("Grafik\BassinkurverLille.png",dpi=600)