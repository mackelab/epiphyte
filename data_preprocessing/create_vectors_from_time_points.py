import numpy as np
import pandas as pd
import sys

sys.path.append("/home/tamara/Documents/DeepHumanVision_pilot/")
from data_base.db_setup import *
import data_preprocessing.pause_handling as pause_handling


def get_index_nearest_timestamp_in_vector(vector, timestamp):
    return (np.abs(vector - int(timestamp))).argmin()  # row number with matching pts


def get_nearest_value_from_vector(vector, timestamp):
    """
    returns the value in vector 'vector' which is closest to the value 'timestamp'
    """
    return vector[(np.abs(vector - (timestamp))).argmin()]  # row number with matching pts


def create_vector_from_start_stop_times_reference_cont_watch(reference_vector, values, starts, stops):
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
        # print("length interval:" , length_interval)
        # print("values i:", values[i])
        ret = np.append(ret, [values[i]] * length_interval)

    return ret


def get_start_stop_times_from_label(neural_rec_time, patient_aligned_label):
    tmp = patient_aligned_label[0]
    values = [tmp]
    start_times = [neural_rec_time[0]]
    stop_times = []
    toggle = 0
    for i in range(1, len(patient_aligned_label)):
        if not patient_aligned_label[i] == tmp:
            values.append(patient_aligned_label[i])
            start_times.append(neural_rec_time[i])
            stop_times.append(neural_rec_time[i - 1])
            tmp = patient_aligned_label[i]
    stop_times.append(neural_rec_time[-1])

    return values, start_times, stop_times


def get_bins_excl_pauses(patient_id, session_nr, neural_rec_time, bin_size):
    start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)
    rec_on = neural_rec_time[0]
    rec_off = neural_rec_time[-1]
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)
    bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)

    return bins_no_pauses


def get_value_matching_timepoint(time_point, values, start_times, end_times):
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point <= start_times[index]:
        index -= 1
    return values[index]


def create_vector_from_start_stop_times_reference(reference_vector, values, starts, stops):
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
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point < start_times[index]:
        if time_point <= start_times[0]:
            return index
        index -= 1
    return values[index]


def get_value_matching_stop_point(time_point, values, start_times, end_times):
    index = get_index_nearest_timestamp_in_vector(end_times, time_point)
    if time_point >= end_times[index]:
        if time_point >= end_times[-1]:
            return index
        index += 1
    return values[index]


def get_index_matching_start_point(time_point, values, start_times, end_times):
    index = get_index_nearest_timestamp_in_vector(start_times, time_point)
    if time_point < start_times[index]:
        if time_point < start_times[0]:
            return index
        index -= 1
    return index


def get_index_matching_stop_point(time_point, values, start_times, end_times):
    index = get_index_nearest_timestamp_in_vector(end_times, time_point)
    if time_point >= end_times[index]:
        if time_point >= end_times[-1]:
            return index
        index += 1
    return index


def get_value_in_time_frame(time_point1, time_point2, values, start_times, end_times):
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