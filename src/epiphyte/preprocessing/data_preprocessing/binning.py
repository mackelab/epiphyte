import os.path
from typing import List, Tuple, Union

import numpy as np

from database.db_setup import *
import annotation.stimulus_driven_annotation.movies.pause_handling as pause_handling
import preprocessing.data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points


def bin_label(
    patient_id: int,
    session_nr: int,
    values: np.ndarray,
    start_times: np.ndarray,
    stop_times: np.ndarray,
    bin_size: int,
    exclude_pauses: bool,
) -> np.ndarray:
    """Bin a label timeline against fixed-size bins.

    :param patient_id: ID of patient.
    :param session_nr: Session number for the movie watching.
    :param values: Values of the label per segment.
    :param start_times: Start times (ms) per segment.
    :param stop_times: Stop times (ms) per segment.
    :param bin_size: Size of one bin in milliseconds.
    :param exclude_pauses: If ``True``, exclude paused playback intervals.
    :returns: Indicator vector (one value per bin).
    """
    neural_rec_time = get_neural_rectime_of_patient(patient_id, session_nr) / 1000

    rec_on = neural_rec_time[0]
    rec_off = neural_rec_time[-1]
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)

    if exclude_pauses:  
        start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)
        bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)
        reference_vector = bins_no_pauses
    else:
        reference_vector = bins

    if os.path.exists("neural_rec_time.npy"):
        os.remove("neural_rec_time.npy")

    return create_vectors_from_time_points.create_vector_from_start_stop_times_reference(reference_vector,
                                                                                         np.array(values),
                                                                                         np.array(start_times),
                                                                                         np.array(stop_times))


def bin_spikes(
    patient_id: int,
    session_nr: int,
    spike_times: np.ndarray,
    bin_size: int,
    exclude_pauses: bool,
    output_edges: bool = False,
) -> Union[np.ndarray, List[np.ndarray]]:
    """Bin spike times into fixed-size bins.

    :param patient_id: ID of the patient.
    :param session_nr: Session number of the experiment.
    :param spike_times: Spike timestamps (ms) as a vector.
    :param bin_size: Bin size in milliseconds.
    :param exclude_pauses: If ``True``, exclude paused playback intervals.
    :param output_edges: If ``True``, also return the bin edges used.
    :returns: Binned spikes or ``[binned_spikes, bin_edges]`` if requested.
    """
    rectime = get_neural_rectime_of_patient(patient_id, session_nr) / 1000
    rec_on = rectime[0]
    rec_off = rectime[-1]
    
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)

    if exclude_pauses:
        start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)

        # rescale pauses from microseconds to milliseconds
        start_times_pauses = start_times_pauses / 1000
        stop_times_pauses = stop_times_pauses / 1000

        # remove the pauses from the binning edges
        bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)
        unit_no_pauses, pause_spks = pause_handling.rm_pauses_spikes(spike_times, start_times_pauses, stop_times_pauses,
                                                                     return_intervals=True)
        # bin spikes
        binned_spikes, _ = np.histogram(unit_no_pauses, bins=bins_no_pauses)

        # output updated to bins without pause
        bins = bins_no_pauses

    else:
        # bin spikes
        binned_spikes, _ = np.histogram(spike_times, bins=bins)

    if output_edges:
        ret = [binned_spikes, bins]
    else: 
        ret = binned_spikes
    
    return ret
