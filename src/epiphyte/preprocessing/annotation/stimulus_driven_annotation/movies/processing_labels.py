import json
import numpy as np
from collections.abc import Sequence
from ....data_preprocessing import create_vectors_from_time_points


def make_label_from_start_stop_times(values: Sequence[int],
    start_times: Sequence[float],
    stop_times: Sequence[float],
    ref_vec: Sequence[float] | np.ndarray,
    default_value: int = 0,
) -> list[int]:
    """
    This function takes a vector with tuples with start and stop times and converts it to the default label

    Args:
        ref_vec (np.ndarray): reference vector, e.g. either PTS of movie or neural recording time of patient
        default_value (int): default value of label, which shall be added to all gaps in start stop times
        values (list): vector with all values
        start_times (list): vector with all start_times of segments
        stop_times (list): vector with all stop times of segments
    Returns:
        list[int] | int: Label vector, or ``-1`` on error.
    """
    if not (len(values) == len(start_times) == len(stop_times)):
        print("vectors values, starts and stops have to be the same length")
        return -1
    
    default_label = [default_value] * len(ref_vec)
    
    for i in range(len(values)):
        start_index_in_default_vec = create_vectors_from_time_points.get_index_nearest_timestamp_in_vector(np.array(ref_vec), start_times[i])
        end_index_in_default_vec = create_vectors_from_time_points.get_index_nearest_timestamp_in_vector(np.array(ref_vec), stop_times[i])

        default_label[start_index_in_default_vec:(end_index_in_default_vec+1)] = \
            [int(values[i])]*(end_index_in_default_vec - start_index_in_default_vec + 1)

    return default_label


def create_xml_for_advene(id_name: str, start_end_times_vector: list[tuple[float, float]], label_name: str) -> str:
    """
    This function creates an XML string, which can be imported to the movie annotation tool Advene

    Args:
        id_name (str): name of ID in XML file
        start_end_times_vector (list): input vector that contains the start and end times of the label in milliseconds
        label_name (str): the name of the label how it shall be displayed in the GUI of Advene

    Returns:
        str: an XML string that can be copied to the content.xml file and loaded to Advene
    """
    new_annotations = ""
    id_ = 0

    for start, end in start_end_times_vector:
        string_new_annotation = '<annotation id="{}{}" type="#{}"><millisecond-fragment begin="{}" end="{}"/><content>num=1</content></annotation>'.format(
            id_name, id_, label_name, int(start * 1000), int(end * 1000))

        new_annotations += string_new_annotation

        id_ += 1
    return new_annotations


def start_stop_values_from_json(path_to_file: str, label_name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    This function extracts start times, stop times and values of all segments of a label from a json file
    
    Args:
        path_to_file (str): path to json file
        label_name (str): name of label (how it was specified in json file)
    Returns:
        np.ndarray, np.ndarray, np.ndarray: first array: values of label, second array: start times of label segments in seconds, third array: stop times of label segments in seconds
    """
    # open and read json file
    with open(path_to_file,'r') as jsonfile:
        labels_json_file = json.load(jsonfile) 
        
    start_times = []
    stop_times = []
    values = []
    # iterate through elements in json file to extract time points of segments
    for annotation in labels_json_file.get("annotations"):
        if annotation.get("type") == label_name:
            start_times.append(annotation.get("begin"))
            stop_times.append(annotation.get("end"))
            values.append(annotation.get("title"))
            
    return np.array(values), np.array(start_times)/1000, np.array(stop_times)/1000


def export_labels_from_json_file(path_to_file: str, label_name: str, bool_save_start_end_times: bool) -> list[int] | int:
    """
    Process a json file from Advene and create a new label.

    Args:
        path_to_file (str): path to json file containing all information about the labels from Advene
        label_name (str): name that was specified in Advene
        bool_save_start_end_times (bool): determine whether the start and end times should be saved as a npy file
    Returns:
        list: new label, aligned with movie (default label)
    """
    with open(path_to_file, 'r') as jsonfile:
        labels_json_file = json.load(jsonfile)

    label_start_end_times = []
    values = []
    for annotation in labels_json_file.get("annotations"):
        if annotation.get("type") == label_name:
            label_start_end_times.append([annotation.get("begin"), annotation.get("end")])
            values.append(annotation.get("title"))

    # if requested, the start and end times will be saved
    if bool_save_start_end_times:
        start_end_times_seconds = [[x / 1000, y / 1000] for [x, y] in label_start_end_times]
        np.save("../useful_data/start_end_times/start_end_times_{}.npy".format(label_name), start_end_times_seconds)

    return label_start_end_times, values


def get_start_stop_times_from_label(neural_rec_time: np.ndarray, patient_aligned_label: np.ndarray) -> tuple[list, list, list]:
    """
    This function takes the patient aligned label and extracts the start and stop times from that.

    Args:
        neural_rec_time (array): neural recording time of patient
        patient_aligned_label (array): patient aligned label
    Returns:
        values (list), start times (list) and stop times (list) of label segments
    """

    tmp = patient_aligned_label[0]
    values = [tmp]
    start_times = [neural_rec_time[0]]
    stop_times = []
    for i in range(1, len(patient_aligned_label)):
        if not patient_aligned_label[i] == tmp:
            values.append(patient_aligned_label[i])
            start_times.append(neural_rec_time[i])
            stop_times.append(neural_rec_time[i-1])
            tmp = patient_aligned_label[i]
    stop_times.append(neural_rec_time[-1])
    
    return values, start_times, stop_times

