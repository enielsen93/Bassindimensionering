# -*- coding: utf-8 -*-

import datetime  # time series management
import matplotlib.dates as dates  # time series management
import numpy as np
import re
import os
from subprocess import call
import bisect  # math bisection method
import dateutil.parser

def __rolling_sum(intensity, window_size):
    window_size = min(len(intensity), window_size)
    ret = np.cumsum(intensity, axis=0, dtype=float)
    ret[window_size:] = ret[window_size:] - ret[:-window_size]
    return np.max(ret[window_size - 1:])

class KM2:
    __timeseries = None

    def __init__(self, kmd_file_path, initial_loss = 0, concentration_time = 0, skip_flags = [], date_criteria = None):
        if type(kmd_file_path) is list or type(kmd_file_path) is tuple:
            gaugetime = kmd_file_path[0]
            gaugeint = kmd_file_path[1]
        else:
            # Read KM2 file as string
            with open(kmd_file_path, 'r') as km2:
                km2Str = km2.readlines()

            # Pre-compile regex search patterns
            eventstartlineRE = re.compile(r"^1 \d{8}")
            eventinfoRE = re.compile(
                r"^1 ?(\d{8}) {0,}(\d{4}) {1,}\d+ {1,}\d+ {1,}(\d+) {1,}([\d\.]+) {1,}([\w\d]+)")
            gaugeintRE = re.compile("([\d\.]+)")

            # Definining vectors for event information
            eventstarttime = []  # The start time of each event
            gaugetime = []  # The time vector of the rain gauge
            gaugeint = []  # The intensity vector of the rain gauge in [mu m/s]
            timedelay = 0
            eventrejected = False

            # Read the KM2 line by line
            for i, line in enumerate(km2Str):
                # If the line contains information about the event:
                if eventstartlineRE.search(line):
                    # Split the information into segments
                    eventinfo = eventinfoRE.match(line)
                    # If it's not rejected ( == 2 ), include it
                    # THIS IS NOW DISABLED: It doesn't appear like this feature works
                    if len(skip_flags) > 0 and any([1 for flag in skip_flags if flag in eventinfo.group(5)]):
                        eventrejected = True
                    else:
                        # Get the start time of the event
                        eventstarttime.append(
                            dates.date2num(
                                datetime.datetime.strptime(
                                    eventinfo.group(1) +
                                    " " +
                                    eventinfo.group(2),
                                    "%Y%m%d %H%M")))
                        # Remember that the next line will be the first registrered intensity for the event, so the first measurement can be excluded
                        # It's not rejected, so don't reject the following measurements
                        eventrejected = False
                        if timedelay > 0:
                            gaugeint.extend([0])
                            gaugetime.extend([eventstarttime[-1] - 1. / 60 / 24])
                            timedelay = 0
                # If the line does not contain information about the event, it must contain intensities.
                # If it's not rejected, read the intensities
                elif not eventrejected:
                    ints = list(map(float, gaugeintRE.findall(line)))
                    # Exclude the first measurement
                    gaugeint.extend(ints)
                    gaugetime.extend((np.arange(0, len(ints), dtype=float) +
                                      timedelay) / 60 / 24 + eventstarttime[-1])
                    timedelay += len(ints)

        if date_criteria:
            date_criteria_dates = [None, None]
            for i in range(len(date_criteria)):
                if type(date_criteria[i]) is datetime.datetime:
                    date_criteria_dates[i] = dates.date2num(date_criteria[i])
                elif type(date_criteria[i]) is str:
                    date_criteria_dates[i] = dates.date2num(dateutil.parser.parse(date_criteria[i]))
                else:
                    date_criteria_dates[i] = dates.date2num(dateutil.parser.parse(date_criteria[i]))

            start_i = bisect.bisect_left(gaugetime, date_criteria_dates[0])
            stop_i = bisect.bisect_right(gaugetime, date_criteria_dates[1])
            gaugetime = gaugetime[start_i:stop_i]
            gaugeint = gaugeint[start_i:stop_i]

        if initial_loss > 0:
            gauge_initial_loss = initial_loss
            import copy
            initial_loss_recovery = (initial_loss/12/1e3)/60*1e3
            gaugeintReduced = copy.deepcopy(gaugeint[:])
            for i in range(len(gaugetime)):
                if (gaugetime[i]-gaugetime[i-1])*24*60>1.5:
                    gauge_initial_loss = min([gauge_initial_loss+
                                            (gaugetime[i]-gaugetime[i-1])*24*60
                                            * initial_loss_recovery,initial_loss])
                gaugeintReduced[i] = max([0,gaugeint[i]-gauge_initial_loss*1e3/60])
                gauge_initial_loss = max([gauge_initial_loss - gaugeint[i]*60/1000,0])
            gaugeint = gaugeintReduced

        if concentration_time>0:
            gaugetime = [np.round(t*24.0*60) for t in gaugetime]

            concentration_time = int(concentration_time)
            gaugetimePadded = []
            gaugeintPadded = []
            timeskips = np.concatenate(([-1],np.where(np.diff(gaugetime)>1.5)[0]))

            for timeskipi in range(1,len(timeskips)):
                gaugetimePadded.extend(gaugetime[timeskips[timeskipi-1]+1:timeskips[timeskipi]+1])
                paddedTimes = [a+gaugetime[timeskips[timeskipi]] for a in
                                        range(1,min([int((gaugetime[timeskips[timeskipi]+1]-gaugetime[timeskips[timeskipi]])),
                                                     concentration_time]))]
                gaugetimePadded.extend(paddedTimes)
                gaugeintPadded.extend(gaugeint[timeskips[timeskipi-1]+1:timeskips[timeskipi]+1])
                gaugeintPadded.extend(np.zeros((len(paddedTimes))))
                # print([int((gaugetime[timeskips[timeskipi]+1]-gaugetime[timeskips[timeskipi]])*60.0*24),concentration_time])
                # A = np.diff(gaugetime)*60*24
                # B = np.diff(gaugetimePadded)*60*24
                # if timeskipi == 2:
                #     break
            gaugetime = gaugetimePadded
            gaugeint = gaugeintPadded
            # print(gaugeint)

            gaugeintTA = np.zeros((len(gaugeint)))

            for i in range(len(gaugeint)):
                iStart = bisect.bisect(gaugetime, gaugetime[i]-concentration_time)

                gaugeintTA[i] = np.sum(gaugeint[iStart:i+1])/concentration_time
            gaugeint = gaugeintTA
            gaugetime = np.array([t/24/60 for t in gaugetime])
        self.gaugetime, self.gaugeint = np.asarray(gaugetime, dtype=float), np.asarray(gaugeint)
        self.rain_gauge_duration = (gaugetime[-1]-gaugetime[0])/365.25

    @property
    def timeseries(self, gaugetime = None, gaugeint = None):
        if gaugetime == None:
            gaugetime = self.gaugetime
        if gaugeint == None:
            gaugeint = self.gaugeint

        if self.__timeseries is None:
            import pandas as pd
            self.__timeseries = pd.Series(gaugeint, index = dates.num2date(gaugetime))
        return self.__timeseries

    def rainStatistics(self, time_aggregate_periods = [], merge_period = None):
        gaugetime_minutes = np.int32(self.gaugetime * 24 * 60)

        if len(time_aggregate_periods) == []:
            merge_period = merge_period if merge_period else 30
        else:
            time_aggregate_periods = [int(t) for t in time_aggregate_periods]
            mergePeriod = max(time_aggregate_periods) if merge_period is None else merge_period

        events_limits = np.where(np.int64(np.round(np.diff(gaugetime_minutes, n=1, axis=0)))>mergePeriod)[0].astype(int)
        events_startindex = np.hstack(([0], events_limits+1))
        events_endindex = np.hstack((events_limits, len(gaugetime_minutes)))

        rain_statistics = np.empty((len(events_startindex), len(time_aggregate_periods)+1), dtype = np.float32)
        for periodi, period in enumerate(time_aggregate_periods):
            rolling_sum = self.timeseries.rolling("%dS" % (period*60)).sum().values

            for event_i in range(len(events_startindex)):
                rain_statistics[event_i, periodi] = np.max(rolling_sum[events_startindex[event_i]:events_endindex[event_i]+1])/1000*60
        for event_i in range(len(events_startindex)):
            rain_statistics[event_i, -1] = np.sum(self.gaugeint[events_startindex[event_i]:events_endindex[event_i]+1])/1000*60
        return rain_statistics, np.transpose(np.vstack((events_startindex, events_endindex)))

    def eventAccRain(self):
        eventidx = 0
        tminutes = np.int32(self.gaugetime * 24 * 60)
        mergePeriod = 60
        # Calculate time diff between each intensitety data point
        tdiff = np.int64(np.round(np.diff(tminutes, n=1, axis=0)))
        eventStartTime = np.empty((0, 1), dtype=np.float)
        # Initialize rain aggregate matrix
        RDAgg = np.empty(1, dtype=np.float)
        # Initialize starttime and stop time for each event
        startj = np.empty((0, 0), dtype=np.int)
        # Loop over all intensity data points
        j = 0
        while j < np.size(tminutes) - 1:
            eventStartTime = np.append(eventStartTime, self.gaugetime[j])
            # End of each event is when there's a dry period of xxx minutes
            jend = np.argmax(tdiff[j:] > mergePeriod) + j
            # Initialize time aggregate set for this event
            RDAgg = np.append(
                RDAgg, np.zeros(
                    (1), dtype=np.float), axis=0)
            # Start time of this event
            startj = np.append(startj, np.int(j))
            # Calculate total rain depth for event
            RDAgg[eventidx] = np.sum(self.gaugeint[j:jend]) / 1000 * 60
            j = jend
            # End time of this event
            j += 1
            eventidx += 1  # Change event index
        return eventStartTime, RDAgg

    def summarize_years(self):
        events_by_year = {}
        events_start_time, RDAgg = self.eventAccRain()
        for event_i in range(len(events_start_time)):
            year = dates.num2date(events_start_time[event_i]).year
            if year in events_by_year:
                events_by_year[year].append(RDAgg[event_i])
            else:
                events_by_year[year] = [RDAgg[event_i]]

        accumulated_rain_by_year = {year: np.sum(events_by_year[year]) for year in events_by_year.keys()}
        return events_by_year, accumulated_rain_by_year

    def plot_IDF(self, time_aggregate_periods, rain_gauge_duration = None):
        if rain_gauge_duration is None:
            rain_gauge_duration = self.rain_gauge_duration
        import matplotlib.pyplot as plt
        rain_depth_aggregated, index = self.rainStatistics(time_aggregate_periods)

        rain_depth_aggregated_sort = np.sort(rain_depth_aggregated, axis=0)
        plt.figure()
        for i in range(len(time_aggregate_periods)):
            plt.plot(np.flipud([rain_gauge_duration/(i+1) for i in range(len(rain_depth_aggregated_sort[:,i]))]), rain_depth_aggregated_sort[:,i]/time_aggregate_periods[i]*1000/60, 'o--', label = "%d min" % time_aggregate_periods[i])
        plt.xlabel(u"Gentagelsesperiode [år]")
        plt.ylabel(r"Intensitet [μm/s]")
        plt.legend()
        plt.grid()
        plt.show()

    def pad_timeseries_with_zeros(self, gaugetime = None, gaugeint = None, pad_length = 1440):
        if gaugetime == None:
            gaugetime = self.gaugetime
        if gaugeint == None:
            gaugeint = self.gaugeint

        timeskips_i = np.where(np.diff(gaugetime) > (2.0 / 24 * 60))[0]

        gaugetime_padded = gaugetime[:]

        for timeskip in timeskips_i:
            additional_time = np.arange(gaugetime[timeskip], gaugetime[timeskip + 1], (1.0 / 24 / 60))
            # additional_intensity = additional_time*0
            gaugetime_padded = np.concatenate((gaugetime_padded, additional_time[:pad_length]))
        gaugeint_padded = np.pad(gaugeint, (0, len(gaugetime_padded) - len(gaugeint)), 'constant', constant_values=0)

        sort_idx = np.argsort(gaugetime_padded)
        gaugetime_padded = gaugetime_padded[sort_idx]
        gaugeint_padded = gaugeint_padded[sort_idx]

        return (gaugetime_padded, gaugeint_padded)

if __name__ == '__main__':
    km2 = KM2(r"C:\Users\ELNN\OneDrive - Ramboll\Documents\Aarhus Vand\Kongelund og Marselistunnel\MIKE\02_RAIN\Viby_godkendte_1979_2018.txt")
    gaugetime,gaugeint = km2.gaugetime,km2.gaugeint
    # print(gaugetime[109:113])
    # print(gaugeint[109:113])
    # a,b = km2.rainStatistics()

    events_start_time, RDAgg = km2.eventAccRain()
    # events_by_year, accumulated_rain_by_year = km2.summarize_years()
    #
    # import matplotlib.pyplot as plt
    # events_5mm_per_year = {year: np.sum([1 for acc_rain in events_by_year[year] if acc_rain >= 5]) for year in events_by_year.keys()}
    # mean_accumulated_rain = np.sum(accumulated_rain_by_year.values()) / 38
    # mean_5mm_events = np.sum([1 for acc_rain in RDAgg if acc_rain >= 5]) / 38
    #
    # plt.bar(accumulated_rain_by_year.keys(), accumulated_rain_by_year.values())
    # plt.hlines(mean_accumulated_rain, np.min(events_by_year.keys()), np.max(events_by_year.keys()))
    #
    # plt.figure()
    # plt.bar(events_5mm_per_year.keys(), events_5mm_per_year.values())
    # plt.hlines(mean_5mm_events, np.min(events_by_year.keys()), np.max(events_by_year.keys()))
    print("Break")
