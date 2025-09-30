"""
Functions related to processing the db stored time points (start/stop/values) into vectors for use in analysis. 
"""

import pandas as pd
import numpy as np

from database.query_functions import *
import annotation.stimulus_driven_annotation.movies.pause_handling as pause_handling

def get_index_nearest_timestamp_in_vector(vector: np.ndarray, timestamp: float) -> int:
    """Finds the index of the value in a vector that is nearest to a given timestamp.

    Args:
        vector (np.ndarray): The array of timestamps to search.
        timestamp (float): The target timestamp to find the nearest value to.
    Returns:
        int: The index of the value in `vector` that is closest to `timestamp`.

    Example:
        ```python
        vector = np.array([1.0, 2.5, 3.8, 5.0])
        idx = get_index_nearest_timestamp_in_vector(vector, 3.0)
        # idx == 1
        ```
    """
    return (np.abs(np.array(vector) - timestamp)).argmin()


def get_nearest_value_from_vector(vector: np.ndarray, timestamp: float) -> float:
    """Finds the value in a vector closest to a given timestamp.

    Args:
        vector (np.ndarray): Array of values to search.
        timestamp (float): Target timestamp to find the nearest value to.

    Returns:
        float: The value from the vector that is closest to the given timestamp.

    Example:
        ```python
        import numpy as np
        vector = np.array([1.0, 2.5, 3.8, 5.0])
        get_nearest_value_from_vector(vector, 4.0)
        3.8
        ```
    """
    return vector[(np.abs(np.array(vector) - (timestamp))).argmin()]  # row number with matching pts


def create_vector_from_start_stop_times_reference_cont_watch(
    reference_vector: np.ndarray,
    values: np.ndarray,
    starts: np.ndarray,
    stops: np.ndarray,
) -> np.ndarray:
    """
    Creates a vector aligned to a reference vector using provided start and stop times and corresponding values.

    This function generates an indicator vector where each segment, defined by its start and stop times, is filled with the associated value. The output vector is aligned to the bins defined by the reference vector, which represents the edges of the bins.

    Args:
        reference_vector (np.ndarray): 
            Array of timestamps or bin edges to which the output vector will be aligned.
        values (np.ndarray): 
            Array of values to assign to each segment.
        starts (np.ndarray): 
            Array of start times for each segment.
        stops (np.ndarray): 
            Array of stop times for each segment.

    Returns:
        np.ndarray: 
            Indicator vector aligned to the reference vector, with values assigned according to the specified intervals.

    Notes:
        Prints an error and returns -1 if the lengths of `values`, `starts`, and `stops` do not match.
    """
    # check if input has the correct format
    if not (len(values) == len(starts) == len(stops)):
        print("vectors values, starts and stops have to be the same length")
        return -1

    nr_intervals = len(values)
    ret = []
    for i in range(0, nr_intervals):
        index_dts_start = get_index_nearest_timestamp_in_vector(reference_vector, starts[i])
        index_dts_stop = get_index_nearest_timestamp_in_vector(reference_vector, stops[i])
        length_interval = index_dts_stop - index_dts_start
        if length_interval == 0:
            ret = np.append(ret, [values[i]])
        else:
            ret = np.append(ret, [values[i]] * (length_interval))

    return ret


def create_vector_from_start_stop_times(
    patient_id: int,
    session_nr: int,
    values: np.ndarray,
    starts: np.ndarray,
    stops: np.ndarray,
) -> np.ndarray:
    """
    Less powerful version of the function create_vector_from_start_stop_times_reference_cont_watch

    Args:
        patient_id (int): ID of patient
        session_nr (int): unique number of session of patient
        values (np.ndarray): array indicating all values in the right order
        starts (np.ndarray): array indicating all start times of all segments in the right order
        stops (np.ndarray): array indicating all stop times of all segments as a vector in the right order
        
    Returns:
        np.ndarray: Indicator function aligned to reference vector.

    """
    neural_rec_time = get_neural_rectime_of_patient(patient_id, session_nr)

    # check if input has the correct format
    if not (len(values) == len(starts) == len(stops)):
        print("vectors values, starts and stops have to be the same length")
        return -1

    nr_intervals = len(values)
    ret = []
    for i in range(0, nr_intervals):
        index_dts_start = get_index_nearest_timestamp_in_vector(neural_rec_time, starts[i])
        index_dts_stop = get_index_nearest_timestamp_in_vector(neural_rec_time, stops[i])
        length_interval = len(neural_rec_time[index_dts_start:index_dts_stop + 1])
        ret = np.append(ret, [values[i]] * length_interval)

    return ret


def get_start_stop_times_from_label(
    neural_rec_time: np.ndarray, patient_aligned_label: np.ndarray
) -> tuple[list, list, list]:
    """
    This function extracts the start and stop times from a label.
    `patient_aligned_label` has to have the same length as `neural_rec_time`
    The time points in the resulting vectors are in neural recording time

    Args:
        neural_rec_time (np.ndarray): array indicating neural recording time
        patient_aligned_label (np.ndarray): array indicating label aligned to patient time

    Returns:
        tuple: ``(values, start_times, stop_times)`` arrays.
    """
    tmp = patient_aligned_label[0]
    values = [tmp]
    start_times = [neural_rec_time[0]]
    stop_times = []
    for i in range(1, len(patient_aligned_label)):
        if not patient_aligned_label[i] == tmp:
            values.append(patient_aligned_label[i])
            start_times.append(neural_rec_time[i])
            stop_times.append(neural_rec_time[i - 1])
            tmp = patient_aligned_label[i]
    stop_times.append(neural_rec_time[-1])

    return values, start_times, stop_times


def get_bins_excl_pauses(
    patient_id: int, session_nr: int, neural_rec_time: np.ndarray, bin_size: int
) -> np.ndarray:
    """
    Returns edges of bins for a given patient with the right bin size, while excluding bins where the movie was paused.

    Args:
        patient_id (int): ID of patient
        session_nr (int): session number
        neural_rec_time (np.ndarray): vector of neural recording time of patient
        bin_size (int): size of bin in milliseconds

    Returns:
        np.ndarray: Edges of bins, excluding paused intervals.
    """
    start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)
    rec_on = neural_rec_time[0]
    rec_off = neural_rec_time[-1]
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)
    bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)

    return bins_no_pauses


def create_vector_from_start_stop_times_reference(
    reference_vector: np.ndarray,
    values: np.ndarray,
    starts: np.ndarray,
    stops: np.ndarray,
) -> np.ndarray:
    """
    Create an indicator function from values, start and stop times of a label aligned to a reference vector of time points. 
    Used to create an indicator function (vector indicating if a labelled feature was present during the interval between two time points) from a set of bin edges. 

    Args:
        reference_vector (np.ndarray): vector of linearly spaced time points (e.g. bin edges)
        values (np.ndarray): values indicating presence or absence of a labeled feature
        starts (np.ndarray): start times of the corresponding values 
        stops (np.ndarray): stop times of the corresponding values

    Returns:
        np.ndarray: indicator function vector.
    """
    # check if input has the correct format
    if not (len(values) == len(starts) == len(stops)):
        print("vectors values, starts and stops have to be the same length")
        return -1

    ret = []

    for i in range(0, len(reference_vector) - 1):
        value = get_value_in_time_frame(time_point1=reference_vector[i], time_point2=reference_vector[i + 1],
                                        values=values, start_times=starts, end_times=stops)
        ret.append(value)

    return ret


def get_value_matching_start_point(
    time_point: float, values: np.ndarray, start_times: np.ndarray, end_times: np.ndarray
) -> float:
    """
    Finds the value in a vector that corresponds to the closest start time less than or equal to a given time point.

    Args:
        time_point (float): the time point for which the value shall be searched
        values (np.ndarray): vector with all values
        start_times (np.ndarray): vector with all start times
        end_times (np.ndarray): vector with all stop times

    Returns:
        float: Value corresponding to the time point.

    """
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point < start_times[index]:
        if time_point <= start_times[0]:
            return index
        index -= 1
    return values[index]


def get_value_matching_stop_point(
    time_point: float, values: np.ndarray, start_times: np.ndarray, end_times: np.ndarray
) -> float:
    """
    Finds the value in a vector that corresponds to the closest stop time less than or equal to a given time point.

    Args:
        time_point (float): the time point for which the value shall be searched
        values (np.ndarray): vector with all values
        start_times (np.ndarray): vector with all start times
        end_times (np.ndarray): vector with all stop times

    Returns:
        float: Value corresponding to the time point.
    """

    index = get_index_nearest_timestamp_in_vector(end_times, time_point)
    if time_point >= end_times[index]:
        if time_point >= end_times[-1]:
            return index
        index += 1
    return values[index]


def get_index_matching_start_point(
    time_point: float, values: np.ndarray, start_times: np.ndarray, end_times: np.ndarray
) -> int:
    """
    Finds the index of the start point that is the closest start point smaller than 'time_point'.

    Args:
        time_point (float): the time point for which the value shall be searched
        values (np.ndarray): vector with all values
        start_times (np.ndarray): vector with all start times
        end_times (np.ndarray): vector with all stop times

    Returns:
        float: Value corresponding to the time point.
    """
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point < start_times[index]:
        if time_point < start_times[0]:
            return index
        index -= 1
    return index


def get_index_matching_stop_point(
    time_point: float, values: np.ndarray, start_times: np.ndarray, end_times: np.ndarray
) -> int:
    """
    Finds the index of the stop point that is the closest stop point greater than 'time_point'.
    
    Args:
        time_point (float): the time point for which the value shall be searched
        values (np.ndarray): vector with all values
        start_times (np.ndarray): vector with all start times
        end_times (np.ndarray): vector with all stop times

    Returns:
        float: Value corresponding to the time point.
    """
    index = get_index_nearest_timestamp_in_vector(end_times, time_point)
    if time_point >= end_times[index]:
        if time_point >= end_times[-1]:
            return index
        index += 1
    return index


def get_value_in_time_frame(
    time_point1: float,
    time_point2: float,
    values: np.ndarray,
    start_times: np.ndarray,
    end_times: np.ndarray,
) -> float:
    """
    Finds the value that is most represented between two time points.
    Needed for creating an indicator function from a set of bin edges with a bin size longer than the frame length, as a bin could contain multiple segments with different values.
    
    Args:
        time_point1 (float): lower bound of time frame         
        time_point2 (float): upper bound of time frame that is regarded
        values (np.ndarray): vector with all values
        start_times (np.ndarray): vector with all start time points
        end_times (np.ndarray): vector with all stop time points

    Returns:
        float: value most represented within the time frame.
    """
    index_1 = get_index_matching_start_point(time_point1, values, start_times, end_times)
    index_2 = get_index_matching_stop_point(time_point2, values, start_times, end_times)
    if index_1 == index_2:
        return values[index_1]
    else:
        df = pd.DataFrame(columns=["value", "weighing"])
        # first interval: add weighing of end_point of this segment - timepoint1
        df = df.append({"value": values[index_1], "weighing": end_times[index_1] - time_point1}, ignore_index=True)
        # all in between intervals: add weighing of length of segment
        for i in range(1, index_2 - index_1):
            if values[index_1 + i] in df.values:
                df.loc[df["value"] == values[index_1 + i], "weighing"] += end_times[index_1 + i] - start_times[
                    index_1 + i]
            df = df.append(
                {"value": values[index_1 + i], "weighing": end_times[index_1 + i] - start_times[index_1 + i]},
                ignore_index=True)
        # last interval: add weighing of timepoint2 - start_point of this segment
        df = df.append({"value": values[index_2], "weighing": time_point2 - start_times[index_2]}, ignore_index=True)

    return list(df[df['weighing'] == df['weighing'].max()]["value"])[0]
