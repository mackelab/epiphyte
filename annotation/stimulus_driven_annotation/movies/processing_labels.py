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

    :param id_name: name of ID in XML file
    :param star_end_times_vector: input vector that contains the start and end times of the label in milliseconds
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


def extract_labels_from_json_file(path_to_file, label_name, bool_save_start_end_times, bool_save_indicator_function=False, path_save_files=None):
    """
    Deprecated, now use start_stop_values_from_json
    """
    with open(path_to_file,'r') as jsonfile:
        labels_json_file = json.load(jsonfile) 
        
    label_start_end_times = []
    for annotation in labels_json_file.get("annotations"):
        if annotation.get("type") == label_name:
            label_start_end_times.append([annotation.get("begin"), annotation.get("end")])

    if bool_save_start_end_times:
        start_end_times_seconds = [[x/1000, y/1000] for [x,y] in label_start_end_times]
        np.save("../useful_data/start_end_times/start_end_times_{}_20200203.npy".format(label_name), start_end_times_seconds)
    
    indicator_function = make_label_from_start_stop_times(label_start_end_times)
    
    if bool_save_indicator_function:
        np.save("../indicators/{}_indicator_fxn_20200203.npy".format(label_name), indicator_function)
    
    if label_start_end_times == []:
        print("No label found in json file. Check the spelling and whether this annotation exists.")
    
    return label_start_end_times, indicator_function


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


def create_default_label_from_advene_json_file(path_to_file, label_name, bool_save_start_end_times):
    """
    whole pipeline from reading in json file to returning new default label
    :param path_to_file: path to json file containing all information about the labels from Advene
    :param label_name: name that was specified in Advene
    :param bool_save_start_end_times: determine whether the start and end times should be saved as a npy file
    :return:
    """
    label_start_stop_times = export_labels_from_json_file(path_to_file, label_name, bool_save_start_end_times)

    return make_label_from_start_stop_times(label_start_stop_times)


def get_start_stop_times_from_label(neural_rec_time, patient_aligned_label):
    tmp = patient_aligned_label[0]
    values = [tmp]
    start_times = [neural_rec_time[0]]
    stop_times = []
    toggle = 0
    for i in range(1,len(patient_aligned_label)):
        if not patient_aligned_label[i] == tmp:
            values.append(patient_aligned_label[i])
            start_times.append(neural_rec_time[i])
            stop_times.append(neural_rec_time[i-1])
            tmp = patient_aligned_label[i]
    stop_times.append(neural_rec_time[-1])
    
    return values, start_times, stop_times


# def get_time_frames_from_patient_aligned_labels():
#     df = pd.DataFrame(columns=["annotator_id", "label_name", "annotation_date", "session_nr", "patient_id", "values", "start_times", "stop_times"])
#     for row in PatientAlignedLabel():
#         annotator_id = row.get("annotator_id")
#         label_name = row.get("label_name")
#         annotation_date = row.get("annotation_date")
#         session_nr = row.get("session_nr")
#         patient_id = row.get("patient_id")
#
#         label_in_patient_time = row.get("label_in_patient_time")
#
#         neural_rec_time = get_neural_rectime_of_patient(patient_id, session_nr) / 1000
#         values_label, start_times_label, stop_times_label = get_start_stop_times_from_label(neural_rec_time, label_in_patient_time)
#
#         start_times_pauses, stop_times_pauses = get_start_stop_times_pauses(patient_id, session_nr)
#         rec_on = neural_rec_time[0]
#         rec_off = neural_rec_time[-1]
#         total_msec = rec_off - rec_on
#         total_bins = int(total_msec / bin_size)
#         bins = np.linspace(rec_on, rec_off, total_bins)
#         bins_no_pauses = pause_handling.rm_pauses_bins(bins, start_times_pauses, stop_times_pauses)
#
#         binned_label = create_vectors_from_time_points.create_vector_from_start_stop_times_reference(bins_no_pauses, np.array(values_label), np.array(start_times_label), np.array(stop_times_label))
#
#         df = df.append({"annotator_id": annotator_id, "label_name": label_name, "annotation_date": annotation_date, "session_nr": session_nr, "patient_id": patient_id, "values": values_label, "start_times": start_times_label, "stop_times": stop_times_label}, ignore_index=True)
#
#     return df


if __name__ == '__main__':
    vec_start_stop = np.load("/home/tamara/Documents/DeepHumanVision_pilot/movie_annotation/useful_data/start_end_times/start_end_times_identical_scene_summer.npy")
    new_label = make_label_from_start_stop_times(vec_start_stop)

    #np.save("/home/tamara/Documents/DeepHumanVision_pilot/movie_annotation/indicators/identical_scenes_new_length_movie.npy", new_label)
