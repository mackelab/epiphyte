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
# former code for this function:  
#     return [default_label[int(round((patient_pts[i]/0.04), 0))] for i in range(0, len(patient_pts))]

    # testing with re-indexing:
    
    return [default_label[(int(round((frame/0.04), 0)) - 1)] for i, frame in enumerate(patient_pts)]


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
