import pandas as pd
import sys

sys.path.append("/home/tamara/Documents/PhD/DeepHumanVision_deploy/")
from database.db_setup import *
import annotation.stimulus_driven_annotation.movies.pause_handling as pause_handling


def get_index_nearest_timestamp_in_vector(vector, timestamp):
    """
    This function returns the index of the value closest to 'timestamp' in 'vector'
    :param vector: array
        vector which shall be searched for 'timestamp'
    :param timestamp: float
        timestamp, which shall be searched
    :return int index
    """
    return (np.abs(np.array(vector) - int(timestamp))).argmin()


def get_nearest_value_from_vector(vector, timestamp):
    """
    This function returns the value in vector 'vector' which is closest to the value 'timestamp'
    :param vector: array
        vector with shall be searched
    :param timestamp: float
        value for which to search
    :return float
    """
    return vector[(np.abs(np.array(vector) - (timestamp))).argmin()]  # row number with matching pts


def create_vector_from_start_stop_times_reference_cont_watch(reference_vector, values, starts, stops):
    """
    This function creates a vector from given start and stop times and values.
    The new vector will be aligned to the reference vector, where the reference vector indicates the edges of the bins.
    :param reference_vector: array
        reference vector at which return vector will be aligned
        reference vector indicates the edges of the bins
    :param values: array
        vector indicating all values in the right order
    :param starts: array
        all start times of all segments as a vector in the right order
    :param stops: array
        all stop times of all segments as a vector in the right order

    :return array
        indicator function aligned to reference vector
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


def create_vector_from_start_stop_times(patient_id, session_nr, values, starts, stops):
    """
    Less powerful version of the function create_vector_from_start_stop_times_reference_cont_watch

    :param patient_id: int
        ID of patient
    :param session_nr: int
        unique number of session of patient
    :param values: array
        vector indicating all values in the right order
    :param starts: array
        all start times of all segments as a vector in the right order
    :param stops: array
        all stop times of all segments as a vector in the right order

    :return array
        indicator function aligned to reference vector

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


def get_start_stop_times_from_label(neural_rec_time, patient_aligned_label):
    """
    This function extracts the start and stop times from a label.
    'patient_aligned_label' has to have the same length as 'neural_rec_time'
    The time points in the resulting vectors are in neural recording time

    :param neural_rec_time: array
        neural recording time
    :param patient_aligned_label: array
        label aligned to patient time

    :return values, start_times, stop_times: arrays
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


def get_bins_excl_pauses(patient_id, session_nr, neural_rec_time, bin_size):
    """
    This function returns edges of bins for a given patient with the right bin size, while excluding bins
    where the movie was paused.

    :param patient_id: int
        ID of patient
    :param session_nr: int
        session number
    :param neural_rec_time: array
        vector of neural recording time of patient
    :param bin_size: int
        size of bin in milliseconds

    :return edges of bins, excluding pauses
    """
    start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)
    rec_on = neural_rec_time[0]
    rec_off = neural_rec_time[-1]
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)
    bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)

    return bins_no_pauses


def create_vector_from_start_stop_times_reference(reference_vector, values, starts, stops):
    """
    This function takes values, start and stop times of segments and creates an indicator function from that

    :param reference_vector: array
        The vector at which the result shall be aligned
    :param values: array
        all values of all segments
    :param starts: array
        all start time points of all segments
    :pram stops: array
        all stop times of all segments

    :return array
        indicator function created from the given input
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


def get_value_matching_start_point(time_point, values, start_times, end_times):
    """
    This function returns the value from the 'values' vector, which is the closest to the given time point 'time_point'
    The 'time_point' hereby refers to a start time

    :param time_point: float
        the time point for which the value shall be searched
    :param values: array
        vector with all values
    :param start_times: array
        vector with all start times
    :param end_times: array
        vector with all stop times

    :return float
        value that corresponds to the given time point

    """
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point < start_times[index]:
        if time_point <= start_times[0]:
            return index
        index -= 1
    return values[index]


def get_value_matching_stop_point(time_point, values, start_times, end_times):
    """
    This function returns the value from the 'values' vector, which is the closest to the given time point 'time_point'
    The 'time_point' hereby refers to a stop time

    :param time_point: float
        the time point for which the value shall be searched
    :param values: array
        vector with all values
    :param start_times: array
        vector with all start times
    :param end_times: array
        vector with all stop times

    :return float
        value that corresponds to the given time point

    """

    index = get_index_nearest_timestamp_in_vector(end_times, time_point)
    if time_point >= end_times[index]:
        if time_point >= end_times[-1]:
            return index
        index += 1
    return values[index]


def get_index_matching_start_point(time_point, values, start_times, end_times):
    """
    This function returns the index of the corresponding start point that is the closest start point smaller than
    'time_point'

    :param time_point: float
        time point for which the index shall be searched
    :param values: array
        vector with all values
    :param start_times: array
        vector with all start times
    :param end_times: array
        vector with all stop times

    :return array
    """
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point < start_times[index]:
        if time_point < start_times[0]:
            return index
        index -= 1
    return index


def get_index_matching_stop_point(time_point, values, start_times, end_times):
    """
    This function returns the index of the corresponding stop point that is the closest stop point greater than
    'time_point'

    :param time_point: float
        time point for which the index shall be searched
    :param values: array
        vector with all values
    :param start_times: array
        vector with all start times
    :param end_times: array
        vector with all stop times

    :return array
    """
    index = get_index_nearest_timestamp_in_vector(end_times, time_point)
    if time_point >= end_times[index]:
        if time_point >= end_times[-1]:
            return index
        index += 1
    return index


def get_value_in_time_frame(time_point1, time_point2, values, start_times, end_times):
    """
    This function returns the value that is most represented between the two time points 'time_point1' and 'time_point2'

    :param time_point1: float
        lower bound of time frame that is regarded
    :param time_point2: fload
        upper bound of time frame that is regarded
    :param values: array
        vector with all values
    :param start_times: array
        vector with all start time points
    :param end_times: array
        vector with all stop time points

    :return int
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