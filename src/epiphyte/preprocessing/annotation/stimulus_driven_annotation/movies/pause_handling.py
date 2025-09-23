"""Helpers to handle pause intervals while binning labels and spikes."""

from typing import List, Tuple

import numpy as np 


def pause_start_bin(bins: np.ndarray, start: float) -> int:
    """Find start bin index inclusive of the pause start.

    :param bins: Bin edges (ms).
    :param start: Pause start time (ms).
    :returns: Index of the start bin.
    """
    ind_start = (np.abs(bins - start)).argmin()  
    if bins[ind_start] > start: 
        start_bin = ind_start - 1
    else: 
        start_bin = ind_start
    return start_bin 


def pause_stop_bin(bins: np.ndarray, stop: float) -> int: 
    """Find stop bin index inclusive of the pause stop.

    :param bins: Bin edges (ms).
    :param stop: Pause stop time (ms).
    :returns: Index of the stop bin.
    """
    ind_stop = (np.abs(bins - stop)).argmin()
    if bins[ind_stop] < stop:
        stop_bin = ind_stop + 1
    else:
        stop_bin = ind_stop
    return stop_bin


def make_pause_interval(bin_start: int, bin_stop: int) -> List[int]:
    """Make a list of indices spanning the pause interval (inclusive)."""
    pause = list(range(bin_start, (bin_stop + 1), 1))
    return pause 


def rm_pauses_bins(
    bins: np.ndarray,
    start: np.ndarray,
    stop: np.ndarray,
    return_intervals: bool = False,
) -> np.ndarray | Tuple[np.ndarray, List[int]]:
    """Remove bin edges that occur during paused playback.

    :param bins: Bin edges (ms).
    :param start: Pause starts (ms).
    :param stop: Pause stops (ms).
    :param return_intervals: If ``True``, also return indices removed.
    :returns: Cleaned bins or ``(bins_no_pauses, removed_indices)``.
    """
    pauses = []
    
    for i in range(len(start)):
        start_bin = pause_start_bin(bins, start[i])
        stop_bin  = pause_stop_bin(bins, stop[i])
        interval = make_pause_interval(start_bin, stop_bin)
        pauses.append(interval)
    
    flatten = lambda l: [item for sublist in l for item in sublist]
    all_pauses = flatten(pauses)
    
    no_pauses = np.delete(bins, all_pauses)
    
    if return_intervals: 
        output = [no_pauses, all_pauses]
    else:
        output = no_pauses
        
    return output


def rm_pauses_spikes(
    unit: np.ndarray,
    start: np.ndarray,
    stop: np.ndarray,
    return_intervals: bool = False,
) -> np.ndarray | Tuple[np.ndarray, List[int]]:
    """Remove spikes that occur during paused playback.

    :param unit: Spike times (ms).
    :param start: Pause starts (ms).
    :param stop: Pause stops (ms).
    :param return_intervals: If ``True``, also return removed indices.
    :returns: Cleaned spikes or ``(unit_no_pauses, removed_indices)``.
    """
    paused_spikes = []

    for i, spk in enumerate(unit): 
        for j in range(len(start)):
            if spk >= start[j] and spk <= stop[j]:
                paused_spikes.append(i)
    
    unit_no_pauses = np.delete(unit, paused_spikes)
    
    if return_intervals: 
        output = [unit_no_pauses, paused_spikes]
    else:
        output = unit_no_pauses
    
    return output
