import os
import numpy as np

import database.config as config
from annotation.stimulus_driven_annotation.movies.watch_log import WatchLog
import re


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


def get_channel_names(path_channel_names):
    """
    This function extracts all channel names from the channel name file
    :param path_channel_names: path to file
    :return: list of channel names
    """
    channel_names = []
    with open(path_channel_names) as f:
        for line in f:
            channel_names.append(line[:-6])
    return channel_names


def get_unit_type_and_number(unit_string):
    """
    This function extracts the different parts of the name of a unit
    e.g.: CSC_MUA1 returns 'M' as unit_type and '1' as unit_nr
    :param unit_string: original unit string
    :return: unity type and unit nr
    """
    if "MUA" in unit_string:
        unit_type = "M"
    elif "SUA" in unit_string:
        unit_type = "S"
    else:
        unit_type = "X"
    unit_nr = unit_string[-1]

    return unit_type, unit_nr


def extract_session_information(session_string):
    """
    This function extracts all relevant information from the name of the folder of a session
    Each folder has the following naming:
    patientID_sessionNr_date_time
    e.g.: 46_1_20151212_10h10m10s
    for session 1 of patient 46, which was recorded on 12th Nov 2015 at 10am.
    :param session_string: string of session
    :return: patient_id, session_nr, date, time
    """
    _, patient_id, session_nr, date, time = session_string.split('_')
    date_processed = date[0:4] + "-" + date[4:6] + "-" + date[6:]
    time_processed = time[0:2] + ":" + time[3:5] + ":" + time[6:8]
    return patient_id, session_nr, date_processed, time_processed


def extract_binned_patient_aligned_label_information(file_name):
    patient_id, label_name, annotator_id, date, _ = file_name.split('_')
    return patient_id, annotator_id, label_name, date


def extract_name_unit_id_from_unit_level_data_cleaning(filename):
    # file name looks something like this: "4stddev_unit0.npy" or more general: "[name]_unit[id]"
    name, unit_id, annotator = filename.split("_")
    unit_id = unit_id[4:]
    annotator = annotator[:-4]
    return name, unit_id, annotator


def extract_information_from_label_name(filename):
    id_, name, annotator, date, category = filename.split("_")
    return id_, name, annotator, date, category


def extract_information_from_continuous_watch_folder(folder):
    for filename in os.listdir(folder):
        if filename.endswith(".npy"):
            if filename.startswith("values"):
                values = np.load(folder + filename)
                _, _, _, annotator_id, annotation_date_ending = filename.split("_")
                annotation_date = annotation_date_ending[:-4]
            if filename.startswith("start_values"):
                start_values = np.load(folder + filename)
            if filename.startswith("stop_values"):
                stop_values = np.load(folder + filename)


def fill_labels(table_name):
    """
    Fill table "table_name" (labels) with all labels from the respective folder
    :param table_name: name of instance of table (should be 'labels')
    :return: None
    """
    directory = "{}/movie_labels/".format(config.PATH_TO_DATA)
    for filename in os.listdir(directory):
        if filename.endswith(".npy"):
            label_id, name, annotator, date, category = filename[:-4].split("_")
            table_name.insert1({'label_id': label_id,
                                'label_name': name,
                                'creator_of_label': annotator,
                                'label': directory + filename,
                                'date': date[0:4] + "-" + date[4:6] + "-" + date[6:8],
                                'category': category
                               }, skip_duplicates=True)


def fill_electrode_units(table_name, patients):
    """
    Fill table "table_name" with all electrode specifications of all patients
    :param table_name: name of table that shall be filled (usually: electrode_units)
    :param patients: name of table containing patient information (usually: patients)
    :return: None
    """
    for session_folder in os.listdir("{}/session_data/".format(config.PATH_TO_DATA)):
        if session_folder.startswith("session"):
            # get the brain regions from the file ChannelNames.txt
            path_channel_names = "{}/session_data/{}/ChannelNames.txt".format(config.PATH_TO_DATA, session_folder)
            channel_names = get_channel_names(path_channel_names)
            patient_id, session_nr, _, _ = extract_session_information(session_folder)
            path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_id) + '/session_' + str(session_nr) + "/"
            i = 0
            try:
                # iterate through all files in the binaries folder to see which units were recorded
                folder_list = []
                for filename in os.listdir(folder):
                    if filename.startswith("CSC"):
                        folder_list.append(filename)
                folder_list.sort(key=natural_keys)

                for filename in folder_list:
                    csc_nr, unit = filename[:-4].split("_")
                    unit_type, unit_nr = get_unit_type_and_number(unit)
                    table_name.insert1({'unit_id': i, 'csc': csc_nr[3:], 'unit_type': unit_type, 'unit_nr': unit_nr,
                                        'patient_id': patient_id,
                                        'brain_region': channel_names[int(csc_nr[3:]) - 1]},
                                       skip_duplicates=True)
                    i += 1

            except Exception as e:
                print("error in fill electorde units:")
                print(e)


def fill_spike_times_movie(table_name, table_electrode_units):
    """
    Fill table "Binaries" with all binary files in the indicated folder, iterating through sub-folders containing
    the binned files
    :param table_electrode_units: table containing information of electrode units (usually: electrode_units)
    :param table_name: name of table that shall be filled (usually: spikes_during_movie
    :return: None
    """
    for session_folder in os.listdir("{}/session_data/".format(config.PATH_TO_DATA)):
        if session_folder.startswith("session"):
            patient_id, session_nr, _, _ = extract_session_information(session_folder)
            path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_id) + '/session_' + str(session_nr) + "/"
            if not os.path.exists(folder):
                os.makedirs(folder)
            try:
                # iterate through all files in the sessions folder and add them to the data base with binning 1
                for filename in os.listdir(folder):
                    if filename.startswith("CSC"):
                        csc_nr, unit = filename[:-4].split("_")
                        unit_type, unit_nr = get_unit_type_and_number(unit)
                        spikes_file = (path_binaries + str(patient_id) + '/session_'  + session_nr + "/" + filename)
                        # print("csc: {}, nr: {}, patient ID: {}, unit_type: {}".format(csc_nr, unit_nr, patient_id, unit_type))
                        unit_id = ((table_electrode_units & "csc = '{}'".format(csc_nr[3:]) & "patient_id='{}'".format(patient_id)
                          & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch("unit_id"))[0]
                        table_name.insert1({'patient_id': patient_id, "unit_id": unit_id,
                                            'session_nr': session_nr, 'spike_times': spikes_file},
                                           skip_duplicates=True)
                        print("Added {} for binning {} of patient {} to data base".format(csc_nr + " " + unit, 1, patient_id))

            except Exception as e:
                print("error in fill spike times movie:")
                print(e)


def fill_binned_spikes(table_name, table_electrode_units):
    for session_folder in os.listdir("{}/session_data/".format(config.PATH_TO_DATA)):
        if session_folder.startswith("session"):
            patient_id, session_nr, _, _ = extract_session_information(session_folder)
            path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_id) + '/session_' + str(session_nr) + "/"
            if not os.path.exists(folder):
                os.makedirs(folder)
            # get all sub-folders in the folder, which contain the binned binaries
            sub_folders = [f.path for f in os.scandir(folder) if f.is_dir()]
            # iterate through sub-folders and add files to data base with respective bin sizes
            for subfolder in sub_folders:
                bin_size = subfolder.split("/")[-1]
                for filename in os.listdir(subfolder + "/"):
                    if filename.startswith("CSC"):
                        csc_nr, unit, _ = filename[:-4].split("_")
                        unit_type, unit_nr = get_unit_type_and_number(unit)
                        unit_id = \
                        ((table_electrode_units & "csc = '{}'".format(csc_nr[3:]) & "patient_id='{}'".format(patient_id)
                          & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch("unit_id"))[0]
                        spikes_file = (subfolder + "/" + filename)
                        table_name.insert1({'patient_id': patient_id, 'bin_size': bin_size, 'unit_id': unit_id,
                                            'session_nr': session_nr, 'spike_vector': spikes_file}, skip_duplicates=True)
                        print("Added {} for binning {} of patient {} to data base".format(csc_nr + " " + unit,
                                                                                          bin_size, patient_id))


def fill_movie_sessions(table_name):
    for folder_name in os.listdir(config.PATH_TO_DATA + "/session_data/"):
        if folder_name.startswith("session"):
            patient_id, session_nr, date, time = extract_session_information(folder_name)
            watchlog_name = config.watchlog_names[patient_id]
            watchlog = WatchLog(config.PATH_TO_DATA + "/patient_data/{}/session_{}/watchlogs/{}".format(patient_id, session_nr, watchlog_name))
            order_movie_frames = watchlog.pts_time_stamps
            path_order_movie_frames = "{}/patient_data/{}/session_{}/order_of_movie_frames/order_of_movie_frames.npy".format(config.PATH_TO_DATA, patient_id, session_nr)
            np.save(path_order_movie_frames, order_movie_frames)
            table_name.insert1({'session_nr': session_nr,
                                'patient_id': patient_id,
                                'date': date,
                                'time': time,
                                'order_movie_frames': path_order_movie_frames
                               }, skip_duplicates=True)


def create_patient_aligned_label(table_movie_sessions, patient_id, session_nr):
    path = config.PATH_TO_DATA + "/movie_labels"
    patient_pts = (table_movie_sessions & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(session_nr)).fetch("order_movie_frames")[0]
    vec_patient_pts = np.load(patient_pts)
    for file_name in os.listdir(path):
        default_label = np.load(path + "/" + file_name)
        patient_aligned_label = match_label_to_patient_pts_time(default_label, vec_patient_pts)
        np.save("{}/patient_aligned_labels/{}/session_{}/{}_{}".format(config.PATH_TO_DATA, patient_id, session_nr, patient_id, file_name), patient_aligned_label)


def match_label_to_patient_pts_time(default_label, patient_pts):
    return [default_label[int(round((patient_pts[i]/0.04), 0))] for i in range(0, len(patient_pts))]


def fill_patient_aligned_labels(table_name):
    # iterate through session folders
    print("function fill_patient_aligned_labels called")
    for folder_name in os.listdir(config.PATH_TO_SESSION_DATA + "/"):
        if folder_name.startswith("session"):
            patient_id, session_nr, date, time = extract_session_information(folder_name)
            # for each session iterate through patient aligned labels and add them to the data base
            path_to_patient_aligned_labels = config.PATH_PATIENT_ALIGNED_LABELS + "/{}/session_{}/".format(patient_id, session_nr)
            for file_name in os.listdir(path_to_patient_aligned_labels):
                if os.path.isfile(path_to_patient_aligned_labels + file_name):
                    print(file_name)
                    patient_id, label_id, label_name, annotator, date, label_class = extract_patient_aligned_label_data_from_file_name(file_name)
                    complete_path_to_file = config.PATH_PATIENT_ALIGNED_LABELS + "/{}/session_{}/{}".format(patient_id, session_nr, file_name)
                    table_name.insert1({'label_id': label_id, 'patient_id': patient_id, 'session_nr': session_nr, 'bin_size': 0,
                                        'label_in_patient_time': complete_path_to_file}, skip_duplicates=True)
                    sub_folders = [f.path for f in os.scandir(path_to_patient_aligned_labels) if f.is_dir()]
                    for subfolder in sub_folders:
                        bin_size = subfolder.split("/")[-1]
                        if len(os.listdir(subfolder + "/")) != 0:
                            for filename in os.listdir(subfolder + "/"):
                                patient_id, label_id, label_name, annotator, date, label_class = extract_patient_aligned_label_data_from_file_name(
                                    filename)
                                complete_path_to_file = config.PATH_PATIENT_ALIGNED_LABELS + "/{}/session_{}/{}".format(patient_id,
                                                                                                                        session_nr,
                                                                                                                        filename)
                                table_name.insert1(
                                    {'label_id': label_id, 'patient_id': patient_id, 'session_nr': session_nr, 'bin_size': bin_size,
                                     'label_in_patient_time': complete_path_to_file}, skip_duplicates=True)


def extract_patient_aligned_label_data_from_file_name(string_file_name):
    patient_id, label_id, label_name, annotator, date, label_class = string_file_name.split("_")
    return patient_id, label_id, label_name, annotator, date[0:4]+"-"+date[4:6]+"-"+date[6:], label_class


def get_list_of_patient_ids(patient_dict):
    list_patient_ids = []
    for i in range(0, len(patient_dict)):
        list_patient_ids.append(patient_dict[i]["patient_id"])

    return list_patient_ids


# def match_pts_to_neural_rec_time(pts, pts_vec, neural_recording_vec):
#     matching_pts = create_vectors_from_time_points.get_nearest_value_from_vector(np.array(pts_vec), pts)
#     indices = [i for i,x in enumerate(pts_vec) if x == matching_pts]
#     ret = []
#     for ind in indices:
#         ret.append(neural_recording_vec[ind])
#     return ret
