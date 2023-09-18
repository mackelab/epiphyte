import json
import numpy as np

import preprocessing.data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points


def make_label_from_start_stop_times(values, start_times, stop_times, ref_vec, default_value=0):
    """
    This function takes a vector with tuples with start and stop times and converts it to the default label
    :param ref_vec: reference vector, e.g. either PTS of movie or neural recording time of patient
    :param default_value: default value of label, which shall be added to all gaps in start stop times
    :param values: vector with all values
    :param start_times: vector with all start_times of segments
    :param stop_times: vector with all stop times of segments
    :return: label (0 and 1 for the length of the movie)
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


def create_xml_for_advene(id_name, start_end_times_vector, label_name):
    """
    This function creates an XML string, which can be imported to the movie annotation tool Advene
    :param id_name: name of ID in XML file
    :param start_end_times_vector: input vector that contains the start and end times of the label in milliseconds
    :param label_name: the name of the label how it shall be displayed in the GUI of Advene
    :return: an XML string, that has to be copied to the content.xml file and loaded to Advene
    """
    new_annotations = ""
    id_ = 0

    for start, end in start_end_times_vector:
        string_new_annotation = '<annotation id="{}{}" type="#{}"><millisecond-fragment begin="{}" end="{}"/><content>num=1</content></annotation>'.format(
            id_name, id_, label_name, int(start * 1000), int(end * 1000))

        new_annotations += string_new_annotation

        id_ += 1
    return new_annotations


def start_stop_values_from_json(path_to_file, label_name):
    """
    This function extracts start times, stop times and values of all segments of a label from a json file
    
    :param path_to_file: path to json file
    :param label_name: name of label (how it was specified in json file)
    :return array, array, array
        first array: values of label
        second array: start times of label segments in seconds
        third array: stop times of label segments in seconds
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


def export_labels_from_json_file(path_to_file, label_name, bool_save_start_end_times):
    """
    processing from json file from Advene to new label
    :param path_to_file: path to json file containing all information about the labels from Advene
    :param label_name: name that was specified in Advene
    :param bool_save_start_end_times: determine whether the start and end times should be saved as a npy file
    :return: new label, aligned with movie (default label)
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


def get_start_stop_times_from_label(neural_rec_time, patient_aligned_label):
    """
    This function takes the patient aligned label and extracts the start and stop times from that
    :param neural_rec_time: neural recording time of patient (array)
    :param patient_aligned_label: patient aligned label (array)
    :return values (list), start times (list) and stop times (list) of label
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

