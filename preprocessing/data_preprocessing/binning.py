import os.path

import annotation.stimulus_driven_annotation.movies.pause_handling as pause_handling
from database.db_setup import *
import preprocessing.data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points


def bin_label(patient_id, session_nr, values, start_times, stop_times, bin_size, exclude_pauses):
    """
    :param patient_id: int
        ID of patient of vector
    :param session_nr: int
        session number of movie watching of patient
    :param values: vector of values of the label
    :param start_times: vector of start times of the label
    :param stop_times: vector of stop times of the label
    :param bin_size: size of one bin in miliseconds
    :param exclude_pauses: bool value whether times of movie play back pausing should be excluded. If exclude_pauses == True: the pauses will be excluded from the binning

    :return: vector that functions as an indicator function. One value for each bin that indicates the label
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


def bin_spikes(patient_id, session_nr, spike_times, bin_size, exclude_pauses):
    """
    This function bins spikes, which are represented as a list of time points
    :param patient_id: the ID of a patient (int)
    :param session_nr: the session number of the experiment (int)
    :param spike_times: a vector (np.array) of time points of spikes
    :param bin_size: the bin size of the binning in milliseconds (int)
    :param exclude_pauses: defining whether pauses in movie play back should be excluded (boolean)
    :return array with binned spikes
    """
    rectime = get_neural_rectime_of_patient(patient_id, session_nr) / 1000
    rec_on = rectime[0]
    rec_off = rectime[-1]

    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)

    if exclude_pauses:
        start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)

        # remove the pauses from the binning edges
        bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)
        unit_no_pauses, pause_spks = pause_handling.rm_pauses_spikes(spike_times, start_times_pauses, stop_times_pauses,
                                                                     return_intervals=True)
        # bin spikes
        binned_spikes, _ = np.histogram(unit_no_pauses, bins=bins_no_pauses)

    else:
        # bin spikes
        binned_spikes, _ = np.histogram(spike_times, bins=bins)

    return binned_spikes

