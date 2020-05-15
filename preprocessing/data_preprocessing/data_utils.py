#!/usr/bin/env python
# coding: utf-8

import numpy as np

NLX_OFFSET = 16 * 1024

nev_type = np.dtype([('', 'V6'),
                     ('timestamp', 'u8'),
                     ('id', 'i2'),
                     ('nttl', 'i2'),
                     ('', 'V38'),
                     ('ev_string', 'S128')])


def nev_read(filename):
    """
    Neuralynx .nev file reading function.
    Returns an array of timestamps and nttls.
    """
    eventmap = np.memmap(filename, dtype=nev_type, mode='r', offset=NLX_OFFSET)
    return np.array([eventmap['timestamp'], eventmap['nttl']]).T


def nev_string_read(filename):
    """
    Neuralynx .nev file reading function.
    Returns an array of timestamps and event strings.
    """
    eventmap = np.memmap(filename, dtype=nev_type, mode='r', offset=NLX_OFFSET)
    return np.array([eventmap['timestamp'], eventmap['ev_string']]).T


def process_movie_events(ev_array):

    wait_for = [1]
    last = 0
    keep = []

    for row in ev_array:
        code = row[1].astype(int)

        if code not in wait_for:
            continue

        elif code in [1, 2, 4, 8, 16, 32, 64, 128]:
            wait_for = [0]
            keep.append(row)

        elif code == 0:

            if last == 128:
                wait_for = [1]
            elif last in [1, 2, 4, 8, 16, 32, 64]:
                wait_for = [last * 2]

        last = code

    return np.array(keep)


def process_events(ev_array):

    onsets = (ev_array[:, 1] == 101).nonzero()[0]
    n_101 = onsets.shape[0]

    # use the first 8 as marker that screening is over
    first_8 = (ev_array[:, 1] == 8).nonzero()[0][0]

    # go back to last 4 before first 8
    last_4 = (ev_array[:first_8, 1] == 4).nonzero()[0][-2]
    # print(first_8, last_4)

    assert n_101 in (4, 8)

    movie_events = ev_array[last_4 + 1:onsets[4], :]
    ret = process_movie_events(movie_events)

    return ret


def getlines(filename):
    with open(filename, 'rb') as logfile:
        data = logfile.read()
    lines = data.splitlines()
    return lines


def read_watchlog(watchlogfile):
    """
    Extracts pts and real times.
    """
    lines = getlines(watchlogfile)
    pts = []
    time = []

    for line in lines[1:]:
        fields  = line.split()
        if len(fields) == 4:
            pts.append(float(fields[1]))
            time.append(int(fields[3]))

    pts = np.array(pts)
    time = np.array(time)
    return pts, time


def read_watchlog_pauses(watchlogfile):
    lines = getlines(watchlogfile)
    start_time = []
    stop_time = []

    for i, line in enumerate(lines):
        fields = line.split()
        first = str(fields[0])
        # print(first)
        if "Pausing" in first:
            # print(line)
            start = i - 1
            start_line = lines[start]
            # print(start_line)
            start_fields = start_line.split()
            start_time.append(int(start_fields[3]))

        if "Continuing" in first:
            # print(line)
            stop = i + 1
            stop_line = lines[stop]
            stop_fields = stop_line.split()
            stop_time.append(int(stop_fields[3]))

        if "Properly" in first:
            start = i - 3
            start_line = lines[start]
            # print(start_line)
            start_fields = start_line.split()
            stop_time.append(int(start_fields[3]))

    return start_time, stop_time


def read_daqlog(daqlogfile):
    """
    Extracts the daq lines.
    """
    lines = getlines(daqlogfile)
    values = []
    pretime = []
    posttime = []

    for line in lines[3:]:
        fields = line.split()
        if len(fields) == 4:
            values.append(int(fields[0]))
            pretime.append(int(fields[2]))
            posttime.append(int(fields[3]))

    values = np.array(values)
    pretime = np.array(pretime)
    posttime = np.array(posttime)

    return values, pretime, posttime


def get_coeff(event_mat, daqlogfile):
    """ loads all the logs, checks and converts """
    eventTimes, eventValues = event_mat[:,0],event_mat[:,1]
    daqValues, daqPretimes, daqPosttimes = read_daqlog(daqlogfile)

    # check events:
    EventErrors = (eventValues != daqValues).sum()
    if EventErrors:
        raise(Warning('Events from 2 logs do not match, {} errors.'.
                      format(EventErrors)))

    # check that daq is quick enough
    diffs = daqPosttimes - daqPretimes
    print("Min Daq Diff: {:.1f} ms, Max Daq Diff: {:.1f} ms".
          format(diffs.min()/1e3, diffs.max()/1e3))

    # convert daqPosttimes to eventTimes by polyfit, check error
    m, b = np.polyfit(daqPosttimes, eventTimes, 1)
    fitdaq = m*daqPosttimes + b
    maxFitError = np.abs(fitdaq-eventTimes).max()/1e3

    print("Maximum Error after Event fit: {:.1f} ms".format(maxFitError))

    return np.array([m, b])


def make_msec(list_usec):
    """ convert a list-like from microseconds (default of event file)
            to milliseconds (default of recording sys)"""
    list_msec = [time / 1000 for i, time in enumerate(list_usec)]
    return list_msec


class TimeConversion(object):
    def __init__(self, path_to_wl, path_to_dl, path_to_events):
        self.path_watchlog = path_to_wl
        self.path_daqlog = path_to_dl
        self.path_evts = path_to_events

    def convert(self):
        event_mat = process_events(nev_read(self.path_evts))
        pts, cpu_time = read_watchlog(self.path_watchlog)
        m, b = get_coeff(event_mat, self.path_daqlog)

        # first convert cpu time to recording system time
        daq_time = cpu_time * m + b
        return pts, daq_time, cpu_time

    def convert_pauses(self):
        start, stop = read_watchlog_pauses(self.path_watchlog)
        event_mat = process_events(nev_read(self.path_evts))
        m, b = get_coeff(event_mat, self.path_daqlog)

        convert_start = [time * m + b for i, time in enumerate(start)]
        convert_stop = [time * m + b for i, time in enumerate(stop)]

        convert_start = make_msec(convert_start)
        convert_stop = make_msec(convert_stop)

        return convert_start, convert_stop