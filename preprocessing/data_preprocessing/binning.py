import sys
import os.path

sys.path.append("/home/tamara/Documents/DeepHumanVision_pilot/")
import data_preprocessing.pause_handling as pause_handling
from data_base.db_setup import *
import data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points


def bin_patient_aligned_label(patient_id, session_nr, label_name, bin_size, annotator_id=None, annotation_date=None):
    dts_patient_path = \
        (MovieSession & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(session_nr)).fetch('cpu_time')[
            0]
    dts_patient = np.load(dts_patient_path) / 1000
    # remove downloaded data
    if os.path.exists(dts_patient_path):
        os.remove(dts_patient_path)

    if annotator_id is not None and annotation_date is not None:
        patient_aligned_label = (PatientAlignedLabel & "patient_id='{}'".format(patient_id) & "label_name='{}'".format(
            label_name) & "annotator_id='{}'".format(annotator_id) & "annotation_date='{}'".format(
            annotation_date)).fetch("label_in_patient_time")[0]
    else:
        patient_aligned_label = \
            (PatientAlignedLabel & "patient_id='{}'".format(patient_id) & "label_name='{}'".format(label_name)).fetch(
                "label_in_patient_time")[0]

    # print(len(dts_patient), len(patient_aligned_label))

    label_dts_patient = dts_patient * patient_aligned_label

    total_msec = dts_patient[-1] - dts_patient[0]
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(dts_patient[0], dts_patient[-1], total_bins)
    label_patient_binned, _ = np.histogram(label_dts_patient, bins=bins)

    return np.array([0 if x == 0 else 1 for x in label_patient_binned])


def bin_patient_aligned_label_excluding_pauses(patient_aligned_label, bin_size, patient_id, session_nr):
    start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)

    # extract neural rec time from data base
    rectime = get_neural_rectime_of_patient(patient_id, session_nr) / 1000
    rec_on = rectime[0]
    rec_off = rectime[-1]
    # get bins
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)

    # remove the pauses from the binning edges
    bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)
    # get unique time stamps so the histogram function works
    bin2 = np.linspace(int(rectime[0]), int(rectime[-1]), len(patient_aligned_label))

    binary_binned, _ = np.histogram(patient_aligned_label * bin2, bins=bins_no_pauses)

    return np.array([0 if x == 0 else 1 for x in binary_binned])


def bin_spikes_and_eliminate_pauses(patient_id, session_nr, spike_times, bin_size):
    start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)

    rectime = get_neural_rectime_of_patient(patient_id, session_nr) / 1000
    rec_on = rectime[0]
    rec_off = rectime[-1]

    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)

    # remove the pauses from the binning edges
    bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)
    unit_no_pauses, pause_spks = pause_handling.rm_pauses_spikes(spike_times, start_times_pauses, stop_times_pauses,
                                                                 return_intervals=True)

    # bin spikes
    binned_spikes, _ = np.histogram(unit_no_pauses, bins=bins_no_pauses)

    return binned_spikes


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

    return create_vectors_from_time_points.create_vector_from_start_stop_times_reference(reference_vector,
                                                                                         np.array(values),
                                                                                         np.array(start_times),
                                                                                         np.array(stop_times))


def bin_spikes(patient_id, session_nr, spike_times, bin_size, exclude_pauses):
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


def bin_one_file(path_binary, save_dir, new_file_name, bins):
    save_dir_abs = os.path.join(save_dir, new_file_name)
    binary = np.load(path_binary)

    if isinstance(bins, np.ndarray) and np.ndim(bins) == 2:
        if bins.shape[1] != 2:
            raise ValueError('If `bins` is a 2d array, the second dim has to be 2 (determines bin edges, so a pair)')
        else:
            binary = np.asarray(binary)
            binary = binary.ravel()
            idxs = binary.searchsorted(bins.ravel())
            binary_binned = np.diff(idxs)
            binary_binned = binary_binned[0:len(binary_binned):2]
    else:
        binary_binned, _ = np.histogram(binary, bins=bins)

    if not os.path.isfile(save_dir_abs):
        np.save(save_dir_abs, binary_binned)
        print("{} binary successful!".format(new_file_name))
    else:
        print("{} binary exists".format(new_file_name))


def univ_bin(pat_id, path_binaries, save_dir, type_prefix, bins, rec_refs_file=None):
    """
    Universal binning function applicable to binaries, indicator fxns...
    :param pat_id : int
    Patient ID
    :param path_binaries : str
    Folder path to where activity during film binaries are
    :param save_dir : str
    Name of the folder where new files are saved
    :param type_prefix : str
    Type of file that is being binned (which determines some extra options).
    :param rec_refs_file : str
    File path to where the file with recording window is
    :param bins: int or sequence of scalars or 2d sequence of scalars
    If bins is an int, it defines the duration of each bin in msec.
    If bins is a sequence, it defines a monotonically increasing array of bin edges, including the rightmost edge,
    allowing for non-uniform bin widths.
    If bins is a 2d sequence, the second dim has to be 2 and it determines bin edges that can also overlap.
    """

    if type_prefix not in ['CSC', 'rectimes', 'scenes']:
        raise ValueError('The file_type should be eihter \'CSC\', \'rectimes\' or \'scenes\'.')

    if isinstance(bins, int):
        if rec_refs_file is None:
            raise ValueError('If bin width is given, there has to be an absolute reference of time (rec_refs_file)')
        else:
            recs = np.load(os.path.join(path_binaries, rec_refs_file))
            total_msec = recs[1] - recs[0]
            total_bins = int(total_msec / bins)
            bins = np.linspace(recs[0], recs[1], total_bins)

    append_name = "_bin{}.npy".format(save_dir)
    save_dir_abs = os.path.join(path_binaries, save_dir)
    if type_prefix != 'CSC':  # either rectime or scenes
        save_dir_abs = os.path.join(save_dir_abs, 'indicators')
    if not os.path.exists(save_dir_abs):
        os.makedirs(save_dir_abs)

    # for filename in os.listdir(os.path.join(path_binaries, str(pat_id))):
    for filename in os.listdir(path_binaries):
        if os.path.isfile(path_binaries + filename):
            # if filename.startswith(type_prefix):http://localhost:8880/?token=bed77b27d6e70ccb3f9e06b8a122c04647b0040c982270d4
            binary = np.load(os.path.join(path_binaries, filename))

            if type_prefix == 'scenes':
                binary = binary / 1000

            if isinstance(bins, np.ndarray) and np.ndim(bins) == 2:
                if bins.shape[1] != 2:
                    raise ValueError(
                        'If `bins` is a 2d array, the second dim has to be 2 (determines bin edges, so a pair)')
                else:
                    binary = np.asarray(binary)
                    binary = binary.ravel()
                    idxs = binary.searchsorted(bins.ravel())
                    binary_binned = np.diff(idxs)
                    binary_binned = binary_binned[0:len(binary_binned):2]
            else:
                binary_binned, _ = np.histogram(binary, bins=bins)

            name = filename[:-4] + append_name

            # this snippet is relevant for indicator functions
            if type_prefix != 'CSC':  # either rectime or scenes
                binary_binned[binary_binned > 0] = 1

            if not os.path.isfile(os.path.join(save_dir_abs, name)):
                np.save(os.path.join(save_dir_abs, name), binary_binned)
                print("{} binary successful!".format(name))
            else:
                print("{} binary exists".format(name))

    name = "bin_edges_{}".format(save_dir)
    np.save(os.path.join(save_dir_abs, name), bins)


def create_binned_vector_from_time_points(patient_id, session_nr, values, start_times, stop_times, bin_size):
    neural_rec_time = get_neural_rectime_of_patient(patient_id, session_nr) / 1000
    start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)
    rec_on = neural_rec_time[0]
    rec_off = neural_rec_time[-1]
    total_msec = rec_off - rec_on
    total_bins = int(total_msec / bin_size)
    bins = np.linspace(rec_on, rec_off, total_bins)
    bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)

    return bins_no_pauses, create_vectors_from_time_points.create_vector_from_start_stop_times_reference(bins_no_pauses,
                                                                                                         np.array(
                                                                                                             values),
                                                                                                         np.array(
                                                                                                             start_times),
                                                                                                         np.array(
                                                                                                             stop_times))


if __name__ == '__main__':
    pat_id = 46

    # path_binaries = "/media/tamara/INTENSO1/data_dhv/spikes/{}/session_1/".format(pat_id)
    path_label = "/media/tamara/INTENSO1/data_dhv/patient_aligned_labels/{}/session_1/".format(pat_id)
    rec_refs_file = "/media/tamara/INTENSO1/data_dhv/spikes/{}/session_1/rec_refs{}.npy".format(pat_id, pat_id)
    bin_size = 1000

    univ_bin(pat_id, path_label, '1000', 'CSC', np.linspace(0, 1, 5625))

