import numpy as np 


def pause_start_bin(bins, start):
    """
    Make sure that the bin labelled as the start of a pause point 
    includes the actual start time, and is not just the nearest point 
    in the bin edges. 
    
    Note: the greater the bin size, the more conservative this makes an estimate. 
    """
    ind_start = (np.abs(bins - start)).argmin()  
    if bins[ind_start] > start: 
        start_bin = ind_start - 1
    else: 
        start_bin = ind_start
    return start_bin 


def pause_stop_bin(bins, stop): 
    """
    Make sure that the bin labelled as the stop of a pause point 
    includes the actual stop time, and is not just the nearest point 
    in the bin edges. 
    
    Note: the greater the bin size, the more conservative this makes an estimate. 
    """
    ind_stop = (np.abs(bins - stop)).argmin()
    if bins[ind_stop] < stop:
        stop_bin = ind_stop + 1
    else:
        stop_bin = ind_stop
    return stop_bin


def make_pause_interval(bin_start, bin_stop):
    """
    Lists out the range of (indices) in the pause between the start and the stop of it. 
    """
    pause = list(range(bin_start, (bin_stop + 1), 1))
    return pause 


def rm_pauses_bins(bins, start, stop, return_intervals=False):
    """
    Remove portions of the binning edges vector which occur during pauses. 
    
    If return_intervals is True, then output contains both the cleaned bins, and the 
    indices corresponding the the pause points. 
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


def rm_pauses_spikes(unit, start, stop, return_intervals=False):
    """
    Remove spikes in a unit vector which occur during a pause. 
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
