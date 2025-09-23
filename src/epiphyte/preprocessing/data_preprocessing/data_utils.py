#!/usr/bin/env python
# coding: utf-8

"""I/O and time-alignment utilities for Neuralynx-like event logs.

Provides helpers to read ``.nev`` (and mock ``.npy``) event files, parse
watchlogs/DAQ logs, and linearly align between local computer time and neural
recording system time.
"""

from pathlib import Path
from typing import List, Tuple

import numpy as np

NLX_OFFSET = 16 * 1024

nev_type = np.dtype([('', 'V6'),
                     ('timestamp', 'u8'),
                     ('id', 'i2'),
                     ('nttl', 'i2'),
                     ('', 'V38'),
                     ('ev_string', 'S128')])


def nev_read(filename: str | Path) -> np.ndarray:
    """Read event timestamps and codes from ``.nev`` or mock ``.npy`` file.

    :param filename: Path to ``.nev`` or mock ``.npy`` array.
    :returns: ``(timestamp, nttl)`` array of shape ``(N, 2)``.
    """
    filename = Path(filename)

    if filename.suffix.lower() == ".nev":
        eventmap = np.memmap(filename, dtype=nev_type, mode='r', offset=NLX_OFFSET)
        ret = np.array([eventmap['timestamp'], eventmap['nttl']]).T
    elif filename.suffix.lower() == ".npy":
        ret = np.load(filename)
    return ret


def nev_string_read(filename: str | Path) -> np.ndarray:
    """Read event timestamps and strings from a ``.nev`` file.

    :param filename: Path to ``.nev`` file.
    :returns: ``(timestamp, ev_string)`` array of shape ``(N, 2)``.
    """
    eventmap = np.memmap(filename, dtype=nev_type, mode='r', offset=NLX_OFFSET)
    return np.array([eventmap['timestamp'], eventmap['ev_string']]).T


def process_movie_events(ev_array: np.ndarray) -> np.ndarray:
    """Filter raw event rows to the movie-event sequence.

    :param ev_array: ``(timestamp, code)`` array.
    :returns: Filtered movie event rows.
    """

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


def process_events(ev_array: np.ndarray) -> np.ndarray:
    """Extract movie-event rows from a full event array.

    :param ev_array: ``(timestamp, code)`` array.
    :returns: Movie-event subset.
    """

    if float(101) in ev_array[:, 1]:
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

    elif not float(0) in ev_array[:,1]:
        ret = ev_array

    return ret


def getlines(filename: str | Path) -> list[bytes]:
    """Read a text file and return the raw lines as bytes.

    :param filename: Path to file.
    :returns: List of lines (bytes).
    """

    with open(filename, 'rb') as logfile:
        data = logfile.read()
    lines = data.splitlines()
    return lines


def read_watchlog(watchlogfile: str | Path) -> Tuple[np.ndarray, np.ndarray]:
    """Extract PTS (s) and CPU times (µs) from a watchlog.

    :param watchlogfile: Path to watchlog created by ffmpeg wrapper.
    :returns: Tuple ``(pts_seconds, cpu_time_us)``.
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


def read_watchlog_pauses(watchlogfile: str | Path) -> Tuple[List[int], List[int]]:
    """Find pause segments in the watchlog.

    :param watchlogfile: Path to pts/CPU watchlog.
    :returns: ``(start_times_us, stop_times_us)`` lists.
    """
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


def read_daqlog(daqlogfile: str | Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract DAQ values and pre/post times.

    :param daqlogfile: Path to DAQ log file.
    :returns: ``(values, pretime_us, posttime_us)`` arrays.
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


def get_coeff(event_mat: np.ndarray, daqlogfile: str | Path) -> np.ndarray:
    """Fit a linear mapping from DAQ post times to event timestamps.

    Loads logs, validates events, and returns slope/intercept.

    :param event_mat: ``(timestamp, code)`` event array.
    :param daqlogfile: Path to DAQ log file.
    :returns: ``[m, b]`` array such that ``timestamp = m*post + b``.
    """
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


def make_msec(list_usec: list[int]) -> list[float]:
    """Convert a list from microseconds to milliseconds.

    :param list_usec: Times in microseconds.
    :returns: Times in milliseconds.
    """

    list_msec = [time / 1000 for i, time in enumerate(list_usec)]
    return list_msec


class TimeConversion(object):
    """Linear mapping between CPU time and neural recording time.

    Enables conversion of stimulus timestamps (e.g., movie frames) to the spike
    time scale.
    """
    
    def __init__(self, path_to_wl: str | Path, path_to_dl: str | Path,
                 path_to_events: str | Path) -> None:
        self.path_watchlog = path_to_wl
        self.path_daqlog = path_to_dl
        self.path_evts = path_to_events

    def convert(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute mapping and convert watchlog times to DAQ times.

        :returns: ``(pts_seconds, dts_ms, cpu_time_us)`` arrays.
        """
    
        event_mat = process_events(nev_read(self.path_evts))
        m, b = get_coeff(event_mat, self.path_daqlog)
        pts, cpu_time = read_watchlog(self.path_watchlog)
        
        # first convert cpu time to recording system time
        daq_time = cpu_time * m + b
        
        return pts, daq_time, cpu_time

    def convert_pauses(self) -> Tuple[List[float], List[float]]:
        """Convert pause CPU timestamps to neural recording time.

        :returns: ``(starts_ms, stops_ms)`` lists in neural recording time.
        """
        start, stop = read_watchlog_pauses(self.path_watchlog)
        event_mat = process_events(nev_read(self.path_evts))
        m, b = get_coeff(event_mat, self.path_daqlog)

        convert_start = [time * m + b for i, time in enumerate(start)]
        convert_stop = [time * m + b for i, time in enumerate(stop)]
        
        #### NOTE: depending on the output set-up, comment/uncomment. 
        ##### Generally, can use the highlights options on the interactive plot
        ##### to indicate if time-scales are not coherent between the data and the 
        ##### pauses. 
        #convert_start = make_msec(convert_start)
        #convert_stop = make_msec(convert_stop)

        return convert_start, convert_stop


    def convert_skips(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Detect skips and return start/stop/value segments in DAQ time.

        :returns: ``(start_values_ms, stop_values_ms, values_idx)`` arrays.
        """
        pts, daq_time, cpu_time = self.convert()
        
        threshold = 1
        max_jump = np.max(np.abs(np.diff(pts)))
        
        
        if max_jump >= threshold:
            print("There is a skip in the movie frame playback that is bigger than {} frames.\nThe biggest skip is {} frames.".format((threshold / 0.04), (max_jump / 0.04)))
            
            # list of indices where the pts jumped by 25+ frames
            beyond_threshold = np.where(np.abs(np.diff(pts)) > threshold)[0]
            print("Timepoints of skips, in neural_rec_time: {}".format(daq_time[beyond_threshold]))
            
            ## setting up start/stop values
            timepoints_of_skips = []
            timepoints_of_skips.append(daq_time[0]) # set first start point to the start of the rec_log

            for index in beyond_threshold:
                timepoints_of_skips.append(daq_time[index])
                timepoints_of_skips.append(daq_time[index + 1])

            timepoints_of_skips.append(daq_time[-1])
            
            ## specifying starts and stops from timepoint collection 
            start_values = timepoints_of_skips[0:-1:2]
            stop_values = timepoints_of_skips[1::2]
            values = np.array(range(0, len(start_values)))
            print("Start timepoints: {}".format(start_values))
            print("Stop timepoints: {}".format(stop_values))
            print("")
            
        else:
            print("There's not any skips in the movie frame playback that are bigger than {} frames.\nThe biggest skip is {} frames.".format((threshold / 0.04), (max_jump / 0.04)))
            print(" ")
            start_values = daq_time[0]
            stop_values = daq_time[-1]
            values = np.array([0])
        
        
        return start_values, stop_values, values
        