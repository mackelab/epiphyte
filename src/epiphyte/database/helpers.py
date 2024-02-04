"""Commonly used query and helper functions"""

import re
import numpy as np

def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def extract_sort_key(filename):
    match = re.match(r'CSC(\d+)_(\w+)(\d*).npy', filename)
    if match:
        csc_number = int(match.group(1))
        mu_su = match.group(2)
        mu_su_number = int(match.group(3)) if match.group(3) else 0
        return csc_number, mu_su, mu_su_number
    else:
        return filename

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
    if "MU" in unit_string:
        unit_type = "M"
    elif "SU" in unit_string:
        unit_type = "S"
    else:
        unit_type = "X"
    unit_nr = unit_string[-1]

    return unit_type, unit_nr


def extract_name_unit_id_from_unit_level_data_cleaning(filename):
    """
    This function splits the name of the unit level data cleaning into its parts
    :param filename: the file name (string)
    :return name: the name of the data cleaning, unit_id: the ID of the unit, annotator: the annotator ID
    """
    # file name looks something like this: "4stddev_unit0.npy" or more general: "[name]_unit[id]"
    name, unit_id, annotator = filename.split("_")
    unit_id = unit_id[4:]
    annotator = annotator[:-4]
    return name, unit_id, annotator


def match_label_to_patient_pts_time(default_label, patient_pts):
    """
    This function matches a label to the patient watch log
    :param default_label: the default movie label as an indicator function (np.array)
    :param patient_pts: indicating the watch behaviour of the patient (np.array)
    :return indicator function aligned to patient pts (np.array)
    """
    
    return [default_label[(int(np.round((frame/0.04), 0)) - 1)] for i, frame in enumerate(patient_pts)]


def get_list_of_patient_ids(patient_dict):
    """
    This function returns all patient IDs
    :param patient_dict: a dictionary in which the patient information is held
    :return list of patient IDs
    """
    list_patient_ids = []
    for i in range(0, len(patient_dict)):
        list_patient_ids.append(patient_dict[i]["patient_id"])

    return list_patient_ids
