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


def tic():
    # Homemade version of matlab tic and toc functions
    import time
    global startTime_for_tictoc
    startTime_for_tictoc = time.time()


def toc():
    import time
    if 'startTime_for_tictoc' in globals():
        print "Elapsed time is " + \
            str(time.time() - startTime_for_tictoc) + " seconds."
    else:
        print "Toc: start time not set"


def readKM2(filename):
        # Read KM2 file as string
    with open(filename, 'r') as km2:
        km2Str = km2.readlines()

    # Pre-compile regex search patterns
    eventstartlineRE = re.compile(r"^1 \d{8}")
    eventinfoRE = re.compile(
        r"^1 ?(\d{8}) {0,}(\d{4}) {1,}\d+ {1,}\d+ {1,}(\d+) {1,}([\d\.]+) {1,}(\d+)")
    gaugeintRE = re.compile("([\d\.]+)")

    # Definining vectors for event information
    eventstarttime = []  # The start time of each event
    gaugetime = []  # The time vector of the rain gauge
    gaugeint = []  # The intensity vector of the rain gauge in [mu m/s]
    timedelay = 0
    eventrejected = False
    eventfirstline = 1

    # Read the KM2 line by line
    for i, line in enumerate(km2Str):
        # If the line contains information about the event:
        if eventstartlineRE.search(line):
            # Split the information into segments
            eventinfo = eventinfoRE.match(line)
            # If it's not rejected ( == 2 ), include it
            # THIS IS NOW DISABLED: It doesn't appear like this feature works
            # like it's supposed to in the KM2 files
            if not eventinfo.group(5) == "4":
                # Get the start time of the event
                eventstarttime.append(
                    dates.date2num(
                        datetime.datetime.strptime(
                            eventinfo.group(1) +
                            " " +
                            eventinfo.group(2),
                            "%Y%m%d %H%M")))
                # Remember that the next line will be the first registrered
                # intensity for the event, so the first measurement can be
                # excluded
                eventfirstline = True
                # It's not rejected, so don't reject the following measurements
                eventrejected = False
                if timedelay > 0:
                    gaugeint.extend([0])
                    gaugetime.extend([gaugetime[-1] + 1. / 60 / 24])
                    timedelay = 0
            # If the event is rejected, remember this
            else:
                eventrejected = True
        # If the line does not contain information about the event, it must contain intensities.
        # If it's not rejected, read the intensities
        elif not eventrejected:
            ints = map(float, gaugeintRE.findall(line))
            # Exclude the first measurement
            if eventfirstline == 1:
                ints = [ints[0]] + ints[1:]
            gaugeint.extend(ints)
            gaugetime.extend((np.arange(0, len(ints), dtype=float) +
                              timedelay) / 60 / 24 + eventstarttime[-1])
            timedelay += len(ints)
            eventfirstline = False
    return np.asarray(gaugetime, dtype=float), np.asarray(gaugeint)


tic()

# Læs KM2-fil
[gaugetime, gaugeint] = readKM2(
    r"K:\Hydrauliske modeller\Regn\Valg af Regn 2018\SilkeborgVandvaerk.km2")

gaugeint = [a*1.3 for a in gaugeint]
# Fjerner initialtab fra regnserie
import copy
initialLoss = 0.6 #mm
initialLossRecovery = 0.0000500/60*1e3
gaugeintReduced = copy.deepcopy(gaugeint[:])
rainevents = 0
jumpTime = []
for i in np.arange(1,len(gaugetime)):
    if (gaugetime[i]-gaugetime[i-1])*24*60>1.5:
        rainevents += 1
        initialLoss = min([initialLoss+
                                (gaugetime[i]-gaugetime[i-1])*24*60
                                * initialLossRecovery,0.6])
        jumpTime.append(initialLoss)
    gaugeintReduced[i] = max([0,gaugeint[i]-initialLoss*1e3/60])
    initialLoss = max([initialLoss - gaugeint[i]*60/1000,0])

# Gentagelsesperiode
RP = [1, 5, 10, 20, 40] # år
# Udløbstal
udlobstal = [1.25] # L/s/ha
# Initialiser volumen-matrix
V = np.empty((len(gaugetime), len(udlobstal)))
# DT (Tidsafstand mellem to maks-værdier
DT = 10

# Initialiser Vmax (matrix for maksimal vandstand)
Vmax = np.empty((100, len(udlobstal)))

print "Progress:"
# Volumen, vandføring ind og ud af bassinet regnes alle i mm
for udlobidx in range(len(udlobstal)): # Kører løkke for alle udløbstal
    print "%d/%d" % (udlobidx+1,len(udlobstal))
    # Start volumen for bassin
    V[(0, udlobidx)] = 0 # Volumen til t = 0 er V = 0

    # Iterer over alle regnnedbør
    for i, t in enumerate(gaugetime):
        # Beregn tidsskridt
        dt = (gaugetime[i] - gaugetime[i - 1]) * 24 * 60  # min [d -> min]
        ind = gaugeintReduced[i] / 1e3 * 60

        # Hvis volumen er over 0, er der vandføring i udløb
        if V[(i - 1, udlobidx)] > 0:
            # Udløb er udløbstal -- Kan ikke overstige bassinvolumen
            # mm [l/s/ha -> mm/min]
            if V[(i - 1, udlobidx)] > 100:
                ud = np.min([udlobstal[udlobidx]*10 / 1e4 *
                         60 * dt, V[(i - 1, udlobidx)]])
            else:
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
print "Årsmiddelnedbør = %1.0f" % (sum(gaugeint) / 1000 * 60 / 39.1)

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



plt.savefig("Grafik\BassinkurverLille.png",dpi=600)