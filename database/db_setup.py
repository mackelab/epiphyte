import datajoint as dj
import numpy as np
import os

from datetime import datetime

import database.config as config
import database.helpers as helpers
import preprocessing.data_preprocessing.data_utils as data_utils
import annotation.stimulus_driven_annotation.movies.processing_labels as processing_labels
import preprocessing.data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points

dhv_schema = dj.schema('db_deploy_mock', locals())

dj.config['stores'] = {
    'shared': dict(
        protocol='s3',
        endpoint='localhost:9000',
        access_key='datajoint',
        secret_key='datajoint',
        bucket='datajoint-demo',
        location=''
    ),
    'local': {  # store in files
        'protocol': 'file',
        'location': os.path.abspath('./dj-store')
    }}


@dhv_schema
class Patient(dj.Lookup):
    definition = """
    # general patient data, imported from config file
    patient_id: int                                    # patient ID
    ---
    age: smallint                                      # age of patient
    gender: enum('m', 'f', 'x')                        # gender of patient
    year: int                                          # year of surgery
    removed_tissue = "unknown" : varchar(32)           # information about removed tissue
    epilepsy_type = "unknown" : varchar(32)            # information about epilepsy type
    additional_information = "" : varchar(128)         # space for additional information
    """

    contents = config.patients


@dhv_schema
class Annotator(dj.Lookup):
    definition = """
    # annatotors of the video, imported from config file
    annotator_id: varchar(5)                    # unique ID for each annotator
    ---
    first_name: varchar(32)                      # first name of annotator
    last_name: varchar(32)                       # last name of annotator
    additional_information="" : varchar(128)     # space for additional information
    """

    contents = config.annotators


@dhv_schema
class LabelProcessingMethod(dj.Lookup):
    definition = """
    # algorithms related to movie annotations
    algorithm_name: varchar(16)                     # unique name for each algorithm
    ---
    description: varchar(128)                    # description of algorithm
    """
    contents = config.algorithms_labels


@dhv_schema
class MovieSession(dj.Imported):
    definition = """
    # data of individual movie watching sessions
    session_nr: int                # session ID
    -> Patient                     # patient ID
    ---
    date : date                    # date of movie session
    time : time
    order_movie_frames: attach     # order of movie frames for patient (watch log) 
    cpu_time: attach               # cpu time stamps (dts)
    neural_recording_time: attach  # neural recording time (rectime)
    channel_names: attach          # list of brain regions
    additional_information = "" : varchar(128)   # space for additional information
    """

    def _make_tuples(self, key):
        for folder_name in os.listdir(config.PATH_TO_DATA + "/session_data/"):
            if folder_name.startswith("session"):
                patient_id, session_nr, date, time = helpers.extract_session_information(folder_name)
                path_wl = "{}/{}/session_{}/watchlogs/{}".format(config.PATH_TO_PATIENT_DATA, patient_id, session_nr,
                                                                 config.watchlog_names[int(patient_id)])
                path_daq = "{}/{}/session_{}/daq_files/{}".format(config.PATH_TO_PATIENT_DATA, patient_id, session_nr,
                                                                  config.daq_names[int(patient_id)])
                for file in os.listdir("{}/{}/session_{}/event_file/".format(config.PATH_TO_PATIENT_DATA, patient_id, session_nr)):
                    if file.startswith("Events"):
                        path_events = "{}/{}/session_{}/event_file/{}".format(config.PATH_TO_PATIENT_DATA, patient_id, session_nr, file)

                time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                            path_to_events=path_events)
                pts, rectime, cpu_time = time_conversion.convert()
                
                cpu_time = cpu_time
                # neural_recording_time = rectime
                
                save_dir = "{}/patient_data/{}/session_{}/order_of_movie_frames/".format(config.PATH_TO_DATA, patient_id, session_nr)

                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                path_order_movie_frames = "{}/patient_data/{}/session_{}/order_of_movie_frames/pts.npy".format(
                    config.PATH_TO_DATA, patient_id, session_nr)
                np.save(path_order_movie_frames, pts)
                path_cpu_time = "{}/patient_data/{}/session_{}/order_of_movie_frames/dts.npy".format(
                    config.PATH_TO_DATA, patient_id, session_nr)
                np.save(path_cpu_time, cpu_time)
                path_neural_rectime = "{}/patient_data/{}/session_{}/order_of_movie_frames/neural_rec_time.npy".format(
                    config.PATH_TO_DATA, patient_id, session_nr)
                np.save(path_neural_rectime, rectime)
                path_channel_names = config.PATH_TO_DATA + "/session_data/" + folder_name + "/ChannelNames.txt"

                self.insert1({'session_nr': session_nr,
                              'patient_id': patient_id,
                              'date': date,
                              'time': time,
                              'order_movie_frames': path_order_movie_frames,
                              'cpu_time': path_cpu_time,
                              'neural_recording_time': path_neural_rectime,
                              'channel_names': path_channel_names
                              }, skip_duplicates=True)


@dhv_schema
class LabelName(dj.Lookup):
    definition = """
    # names of existing labels, imported from config file
    label_name: varchar(32)   # label name
    """

    contents = config.label_names


@dhv_schema
class MovieAnnotation(dj.Imported):
    definition = """
    # information about video annotations (e.g. labels of characters); 
    # this table contains start and end time points and values of the segments of the annotations;
    # all time points are in Neural Recording Time;
    -> Annotator   # creator of movie annotation
    -> LabelName   # name of annotation
    annotation_date: date    # date of annotation
    ---
    values: longblob       # list of values that represent label
    start_times: longblob  # list of start times of label segments in movie play time (PTS)
    stop_times: longblob   # list of stop times of label segments in movie play time (PTS)
    category: varchar(32)  # category of label; e.g. 'character', 'emotion', 'location'
    indicator_function: longblob # full indicator function, one value for each movie frame
    additional_information="":varchar(30) # space for additional information
    """

    def _make_tuples(self, key):
        directory = "{}/movie_annotation/".format(config.PATH_TO_DATA)
        for filename in os.listdir(directory):
            if os.path.isfile(directory + filename) and filename.endswith(".npy"):
                label_id, name, annotator, date, category = filename[:-4].split("_")
                content = np.load("{}{}".format(directory, filename))
                
                values = np.array(content[0])
                start_times = np.array(content[1])
                stop_times = np.array(content[2])
                
                ind_func = processing_labels.make_label_from_start_stop_times(values, start_times, stop_times, config.PTS_MOVIE_new)
                
                self.insert1({'label_name': name,
                      'annotator_id': annotator,
                      'annotation_date': date[0:4] + "-" + date[4:6] + "-" + date[6:8],
                      'category': category,
                      'values': values,
                      'start_times': start_times,
                      'stop_times': stop_times,
                      'indicator_function': np.array(ind_func)
                      }, skip_duplicates=True)
                print("Added label {} to database.".format(name))

            
@dhv_schema
class ElectrodeUnit(dj.Imported):
    definition = """
    # Contains information about the implanted electrodes of each patient
    -> Patient                       # patient ID
    unit_id: int                     # unique ID for unit (for respective  patient)
    ---
    csc: int                         # number of CSC file
    unit_type: enum('M', 'S', 'X')   # unit type: 'M' for Multi Unit, 'S' for Single Unit, 'X': undefined
    unit_nr: int                     # number of unit, as there can be several multi units and single units in one CSC file
    brain_region: varchar(8)         # brain region where unit was recorded
    additional_information = "" : varchar(128)   # space for additional information
    """

    def _make_tuples(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")

        #TODO: reformat test with multiple session data 
        for index_session in range(0, len(patient_ids)):
        
            path_binaries = '{}/patient_data/'.format(config.PATH_TO_DATA)
            path_channels = '{}/session_data/'.format(config.PATH_TO_DATA)
            folder_channels = "session_{}_{}".format(patient_ids[index_session], session_nrs[index_session])
            
            complete_session_name = []
            for session_folder in os.listdir(path_channels):
                if session_folder.startswith(folder_channels):
                    channel_names = helpers.get_channel_names(os.path.join(path_channels, "{}/ChannelNames.txt".format(session_folder)))
                    complete_session_name.append(session_folder)
                        
            # iterate through all files in the binaries folder to see which units were recorded
            folder_list = []
            
            dir_w_dir = os.path.join(config.PATH_TO_DATA, "patient_data", str(patient_ids[index_session]), "session_{}".format(session_nrs[index_session]))
            
            folder_spikes_nm = []
            for folder in os.listdir(dir_w_dir):
                if folder.startswith("spik"):
                    # accounting for differences in file structure btw mock and real data
                    folder_spikes_nm.append(folder)
                
            dir_w_spikes = os.path.join(config.PATH_TO_DATA, "patient_data", str(patient_ids[index_session]), "session_{}".format(session_nrs[index_session]), folder_spikes_nm[0])
            
            for filename in os.listdir(dir_w_spikes):
                if filename.startswith("CSC"):
                    folder_list.append(filename)
                    
            folder_list.sort(key=helpers.natural_keys)

            for index, filename in enumerate(folder_list):
                csc_nr, unit = filename[:-4].split("_")
                print(csc_nr, int(csc_nr[3:]) - 1)
                print(channel_names[index])
                unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
                self.insert1({'unit_id': index, 'csc': csc_nr[3:], 'unit_type': unit_type, 'unit_nr': unit_nr,
                              'patient_id': patient_ids[index_session],
                              'brain_region': channel_names[index]},
                             skip_duplicates=True)


@dhv_schema
class SpikeTimesDuringMovie(dj.Imported):
    definition = """
    # This table contains all spike times of all units of all patients in Neural Recording Time
    # Each entry contains a vector of all spike times of one unit of one patient
    -> ElectrodeUnit                # unit from which data was recorded
    -> MovieSession                 # session ID
    ---
    spike_times: attach              # in case bin_size is not 0: number of spikes; otherwise: times of spikes (original data)
    """

    def _make_tuples(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
        
        for index_session in range(0, len(patient_ids)):
            
#             path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
#             folder = path_binaries + str(patient_ids[index_session]) + '/session_' + str(
#                 session_nrs[index_session]) + "/"
            
#             if not os.path.exists(folder):
#                 os.makedirs(folder)
                
            path_binaries = '{}/patient_data/'.format(config.PATH_TO_DATA)
            path_channels = '{}/session_data/'.format(config.PATH_TO_DATA)
            folder_channels = "session_{}_{}".format(patient_ids[index_session], session_nrs[index_session])
            
            # iterate through all files in the binaries folder to see which units were recorded
            folder_list = []
            
            dir_w_dir = os.path.join(config.PATH_TO_DATA, "patient_data", str(patient_ids[index_session]), "session_{}".format(session_nrs[index_session]))
            
            # get name of directory with spiking data inside (any file with "spik" as start)
            # accounting for differences in file structure btw mock and real data
            folder_spikes_nm = []
            for folder in os.listdir(dir_w_dir):
                if folder.startswith("spik"):
                    folder_spikes_nm.append(folder)
                
            dir_w_spikes = os.path.join(config.PATH_TO_DATA, "patient_data", str(patient_ids[index_session]), "session_{}".format(session_nrs[index_session]), folder_spikes_nm[0])
             
            # iterate through all files in the sessions folder and add them to the data base
            for filename in os.listdir(dir_w_spikes):
                if filename.startswith("CSC"):
                    file_name_only, file_extension = os.path.splitext(filename)
                    
                    csc_nr, unit = file_name_only.split("_")
                    unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
#                     spikes_file = (path_binaries + str(patient_ids[index_session]) + '/session_' + str(session_nrs[index_session]) + "/" + filename)
                    spikes_file = os.path.join(config.PATH_TO_DATA, "patient_data", str(patient_ids[index_session]), "session_{}".format(session_nrs[index_session]), folder_spikes_nm[0], filename)
                    # TODO: check which file types should be expected for the spiking data import 
                    #print(spikes_file)
                    
                    unit_id = ((ElectrodeUnit & "csc = '{}'".format(csc_nr[3:]) & "patient_id='{}'".format(patient_ids[index_session])
                                & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch("unit_id"))[0]
                    self.insert1({'patient_id': patient_ids[index_session], "unit_id": unit_id,
                                  'session_nr': session_nrs[index_session], 'spike_times': spikes_file}, skip_duplicates=True)
                    #print("Added spikes from {} of patient {} to data base".format(csc_nr + " " + unit, patient_ids[index_session]))


@dhv_schema
class ProcessedMovieAnnotation(dj.Computed):
    definition = """
    # This table contains information about processed annotations, so different algorithms can be used to for example average labels
    -> LabelName
    -> LabelProcessingMethod
    last_entry_date: date    # date of most recent annotation entry
    ---
    processed_frames: longblob   # processed annotation on frames
    """

    class Entry(dj.Part):
        definition = """
        -> master
        -> MovieAnnotation
        """

    @property
    def key_source(self):
        # dj.U() is used to promote a non primary-key column into a primary key column
        return dj.U('last_entry_date') * (
                    LabelName.aggr(MovieAnnotation, last_entry_date='MAX(annotation_date)') * LabelProcessingMethod)

    def make(self, key):
        base_key = dict(key)  # make a copy for Part table entries
        if key['proc_method'] == 'method1':
            entry_keys, labeled_frames = (MovieAnnotation & key).fetch('KEY', 'labeled_frames')
            key['processed_frames'] = np.stack(labeled_frames).mean(axis=0)
            self.insert1(key)
            entry_keys = [dict(k, **base_key) for k in entry_keys]  # add master's columns into entry_keys
            self.Entry.insert(entry_keys)

    
@dhv_schema
class PatientAlignedMovieAnnotation(dj.Computed):
    definition = """
    # Movie Annotations aligned to patient time / time points are in neural recording time
    -> MovieAnnotation     # label
    -> MovieSession        # movie watching session ID
    ---
    label_in_patient_time: longblob    # label matched to patient time (pts)
    values: longblob       # list of values that represent label
    start_times: longblob  # list of start times of label segments in neural recording time
    stop_times: longblob   # list of stop times of label segments in neural recording time
    additionl_information="":varchar(30)
    """

    def make(self, key):
        entry_key_video_annot, original_label = (MovieAnnotation & key).fetch('KEY', 'indicator_function')
        entry_key_movie_session, pts_vec = (MovieSession & key).fetch("KEY", 'order_movie_frames')
        
        patient_aligned_label = helpers.match_label_to_patient_pts_time(default_label=original_label[0], patient_pts=np.load(pts_vec[0]) )
        neural_rec_time = get_neural_rectime_of_patient(entry_key_movie_session[0]['patient_id'], entry_key_movie_session[0]['session_nr'])
        values, starts, stops = create_vectors_from_time_points.get_start_stop_times_from_label(neural_rec_time, patient_aligned_label)
        
        self.insert1({'annotator_id': entry_key_video_annot[0]['annotator_id'],
                      'label_name': entry_key_video_annot[0]['label_name'],
                      'annotation_date': entry_key_video_annot[0]['annotation_date'],
                      'patient_id': entry_key_movie_session[0]['patient_id'],
                      'session_nr': entry_key_movie_session[0]['session_nr'],
                      'label_in_patient_time': np.array(patient_aligned_label),
                      'values': np.array(values),
                      'start_times': np.array(starts),
                      'stop_times': np.array(stops),
                     }, skip_duplicates=True)
            
        print("Added patient aligned label {} to database.".format(entry_key_video_annot[0]['label_name']))

## TODO: potentially remove? does this expect binaires stored as npy to run?
@dhv_schema
class UnitLevelDataCleaning(dj.Imported):
    definition = """
    # Contains information about data cleaning on a unit-level
    -> ElectrodeUnit                   # respective unit
    -> MovieSession                    # number of movie session
    -> Annotator                       # who created the cleaning?
    name: varchar(16)                  # unique name for data cleaning
    ---
    data: attach                       # actual data
    description = "" : varchar(128)    # description of data cleaning
    """

    def _make_tuples(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
        for index_session in range(0, len(patient_ids)):
            path_binaries = '{}/unit_level_data_cleaning/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_ids[index_session]) + '/session_' + str(
                session_nrs[index_session]) + "/"
            if not os.path.exists(folder):
                os.makedirs(folder)
            for filename in os.listdir(folder):
                if filename.endswith(".npy"):
                    name, unit_id, annotator = helpers.extract_name_unit_id_from_unit_level_data_cleaning(filename)
                    if name == '4stddev':
                        description = "removing all bins where the firing rate is greater than 4 std dev from mean"
                    elif name=="smoothed4stddev":
                        description = "removing all bins where smoothed firing rate is greater than 4 std dev from mean"
                    else:
                        description = ""
                    self.insert1({'patient_id': patient_ids[index_session], "unit_id": unit_id, "annotator_id": annotator,
                                  'session_nr': session_nrs[index_session], "description": description, "name": name,
                                  'data': "{}/{}".format(folder, filename)},
                                 skip_duplicates=True)

##  TODO: decide if this table should removed for deploy version
@dhv_schema
class PatientLevelDataCleaning(dj.Manual):
    definition = """
    # Contains information about data cleaning on a patient-level 
    # (e.g. annotated time frames, where all units are firing too high)
    -> MovieSession                    # number of movie session
    -> Annotator                       # who created the cleaning?
    name: varchar(16)                  # unique name for data cleaning
    ---
    data: attach                       # actual data
    description = "" : varchar(128)    # description of data cleaning
    """


@dhv_schema
class MovieSkips(dj.Computed):
    definition = """
    # This table Contains start and stop time points, where the watching behaviour of the patient changed from 
    # continuous (watching the movie in the correct frame order) to non-continuous (e.g. jumping through the movie) or 
    # the other way round:;
    # all time points are in Neural Recording Time
    -> MovieSession                    # number of movie session
    ---
    values: longblob                   # values of continuous watch segments
    start_times: longblob              # start time points of segments
    stop_times: longblob               # end time points of segments
    notes = "" : varchar(128)          # further notes
    """
    
    def make(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
        
        for i in range(len(patient_ids)):
            path_wl = "{}/{}/session_{}/watchlogs/{}".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i],
                                                             config.watchlog_names[int(patient_ids[i])])
            path_daq = "{}/{}/session_{}/daq_files/{}".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i],
                                                              config.daq_names[int(patient_ids[i])])
            # bridge btw .npy and .nev file types for Events file
            for file in os.listdir("{}/{}/session_{}/event_file/".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i])):
                    if file.startswith("Events"):
                        path_events = "{}/{}/session_{}/event_file/{}".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i], file)
            
            time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                        path_to_events=path_events)
            
            starts, stops, values = time_conversion.convert_skips()
            
            notes = "time points of continuous watch, extracted from watch log - {}".format(datetime.today())
             
            self.insert1(
                {'patient_id': patient_ids[i], 'session_nr': session_nrs[i], "notes": notes,
                 'start_times': np.array(starts), 'stop_times': np.array(stops), 'values': np.array(values)
                 },
                skip_duplicates=True)
            
                    
@dhv_schema
class MoviePauses(dj.Computed):
    definition = """
    # This table contains information about pauses in movie playback;
    # This is directly computed from the watch log;
    # Time points are in Neural Recording Time
    -> MovieSession                    # movie watching session of patient
    ---
    start_times: longblob              # start time points of pauses
    stop_times: longblob                # end time points of pauses
    description = "" : varchar(128)    # description 
    further_information = "":varchar(128) # space for further information
    """

    def make(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")

        for i in range(len(patient_ids)):
            path_wl = "{}/{}/session_{}/watchlogs/{}".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i],
                                                             config.watchlog_names[int(patient_ids[i])])
            path_daq = "{}/{}/session_{}/daq_files/{}".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i],
                                                              config.daq_names[int(patient_ids[i])])
            # bridge btw .npy and .nev file types for Events file
            for file in os.listdir("{}/{}/session_{}/event_file/".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i])):
                    if file.startswith("Events"):
                        path_events = "{}/{}/session_{}/event_file/{}".format(config.PATH_TO_PATIENT_DATA, patient_ids[i], session_nrs[i], file)
                        
            time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                        path_to_events=path_events)
            start, stop = time_conversion.convert_pauses()

            description = "time points of pauses, extracted from watch log - {}".format(datetime.today())

            self.insert1(
                {'patient_id': patient_ids[i], 'session_nr': session_nrs[i], "description": description,
                 'start_times': np.array(start), 'stop_times': np.array(stop)
                 },
                skip_duplicates=True)

            
@dhv_schema
class ManualAnnotation(dj.Manual):
    definition = """
    -> MovieSession                    # number of movie session
    -> Annotator                       # who created the cleaning?
    label_entry_date: date             # date of creation of label
    name: varchar(32)
    ---
    x_zero: longblob                   # x0 coordinate of all boxes
    x_one: longblob                    # x1 coordinate of all boxes
    y_zero: longblob                   # y0 coordinate of all boxes
    y_one: longblob                    # y1 coordinate of all boxes
    additional_information="": varchar(46) # further notes
    """


#######################
# Retrieval Functions #
#######################

def get_brain_region(patient_id, unit_id):
   # name_vec = (ElectrodeUnit & "patient_id='{}'".format(patient_id) & "unit_id='{}'".format(unit_id)).fetch('brain_region')[0]
    
#     region = np.load(name_vec)
    
#     if os.path.exists(name_vec):
#         os.remove(name_vec)  
    
    return (ElectrodeUnit & "patient_id='{}'".format(patient_id) & "unit_id='{}'".format(unit_id)).fetch('brain_region')[0]

def get_dts_of_patient(patient_id, session_nr):
    """
    Get dts of patient (cpu time), which is the time stamp matching the local time during the experiment
    :param patient_id: ID of patient
    :param session_nr: number of movie watch session
    :return: vector of cpu time that correspond to pts time stamps (extracted from watch log)
    """
    print("Note: Divide the patient dts vector by 1000 to get milliseconds")
    
    name_vec = (MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch("cpu_time")[0]
    
    dts = np.load(name_vec)
    
    if os.path.exists(name_vec):
        os.remove(name_vec)   
    
    return dts

def get_info_continuous_watch_segments(patient_id, session_nr):
    """
    This function returns the start times, stop times and values of the continuous watch segment
    :param patient_id: ID of patient (int)
    :param session_nr: session number of experiment (int)
    :param annotator_id: ID of annotator (string)
    :param annotation_date: data of annotation (date)
    :return start times, stop times, values
    """
    values, starts, stops = (MovieSkips() & "patient_id={}".format(patient_id) & "session_nr={}".format(session_nr)).fetch('values', 'start_times', 'stop_times')
    return values[0], starts[0], stops[0]


def get_neural_rectime_of_patient(patient_id, session_nr):
    """
    Get neural recording time of patient
    :param patient_id: ID of patient
    :param session_nr: number of movie watch session
    :return: vector of neural recording time that correspond to pts time stamps
    """
    name_vec = (MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch("neural_recording_time")[0]
    
    rectime = np.load(name_vec)
    
    if os.path.exists(name_vec):
        os.remove(name_vec)   
    
    return rectime


def get_number_of_units_for_patient(patient_id):
    """
    this function returns the number of recorded units from a patient
    :param patient_id: patient ID (int)
    :return int value, number of recorded units
    """
    name_vec = ((Patient.aggr(ElectrodeUnit.proj(), number_of_units="count(*)")) & "patient_id='{}'".format(patient_id)).fetch("number_of_units")[0]
   
    return name_vec


def get_original_movie_label(label_name, annotation_date, annotator_id):
    """
    This function returns the original movie label from the database
    
    TODO: does this still work with new storage method? 
    
    :param label_name: name of the label (string)
    :param annotation_date: date of annotation (date)
    :param annotator_id: ID of annotator (int)
    :return extracted vector from database (np.array)
    """
    name_vec = (MovieAnnotation() & "label_name='{}'".format(label_name) & "annotator_id='{}'".format(annotator_id) & "annotation_date='{}'".format(annotation_date)).fetch("indicator_function")[0]
       
    return name_vec

def get_patient_aligned_annotations(patient_id, label_name, annotator_id, annotation_date):
    """
    This function returns the values, start, and stop times.  
    
    :param patient_id: number of patient (int)
    :param label_name: name of the label (string)
    :param annotator_id: ID of annotator (int)
    :param annotation_date: date of annotation (date)
    
    :return 
     - values (np.array)
     - starts (np.array)
     - stops (np.array)
    """
    
    values, starts, stops = (PatientAlignedMovieAnnotation() & "label_name='{}'".format(label_name) & "annotator_id='{}'".format(annotator_id) & "annotation_date='{}'".format(annotation_date) &  "patient_id='{}'".format(patient_id)).fetch("values", "start_times", "stop_times")
    
    values = values[0]
    starts = starts[0] / 1000
    stops  = stops[0] / 1000
    
    return values, starts, stops

#### unnecessary?
def get_patient_level_cleaning_vec_from_db(patient_id, session_nr, name_of_vec, annotator_id):
    """
    This function returns the patient level cleaning vector from the database
    :param patient_id: patient ID (int)
    :param session_nr: session number of experiment (int)
    :param name_of_vec: name of the vector that should be extracted (string)
    :param annotator_id: ID of annotator of annotation (string)
    :return extracted vector from database (np.array)
    """
    name_pts_cont_watch = (PatientLevelDataCleaning() & "name='{}'".format(name_of_vec)
                           & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(session_nr)
                           & "annotator_id='{}'".format(annotator_id)).fetch("data")[0]
    cont_watch = np.load(name_pts_cont_watch)
    
    if os.path.exists(name_pts_cont_watch):
        os.remove(name_pts_cont_watch)
        
    return cont_watch

def get_patient_level_data_cleaning(patient_id, session_nr, vector_name):
    """
    :param patient_id: patient ID (int)
    :param session_nr: session number of experiment (int)
    :param vector_name: name ov the patient level cleaning vector (string)
    :return extracted vector from database (np.array)
    """
    name_pts_cont_watch = \
    (PatientLevelDataCleaning() & "name='{}'".format(vector_name) & "patient_id = '{}'".format(patient_id) & "session_nr='{}'".format(session_nr)).fetch("data")[0]
    cont_watch = np.load(name_pts_cont_watch)
    os.remove(name_pts_cont_watch)

    return cont_watch

####

def get_pts_of_patient(patient_id, session_nr):
    """
    Get the order of the movie in the way the patient watched it
    :param patient_id: ID of patient
    :param session_nr: number of movie watch session
    :return: vector of movie frames in the order the patient watched the movie
    """
    name_vec = (MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch("order_movie_frames")[0]
    pts = np.load(name_vec)
    
    if os.path.exists(name_vec):
        os.remove(name_vec)  
    
    return pts

def get_spiking_activity(patient_id, session_nr, unit_id):
    """
    Extract spiking vector from data base.
    :param patient_id: ID of patient
    :param session_nr: session number
    :param unit_id: Unit ID of which spiking activity shall be extracted
    """
    try:
        spikes = (SpikeTimesDuringMovie & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(
            session_nr) & "unit_id='{}'".format(unit_id)).fetch("spike_times")[0]
    except:
        print("The spiking data you were looking for doesn't exist in the data base.")
        return -1

    spike_vec = np.load(spikes)

    if os.path.exists(spikes):
        os.remove(spikes)

    return spike_vec

def get_spikes_from_brain_region(patient_id, session_nr, brain_region):
    """
    this function extracts all spiking vectors from a specific brain region
    :param patient_id: patient ID (int)
    :param session_nr: session number of experiment (int)
    :param brain_region: brain region of interest in its abbreviation (str)
    :return spike times from brain region (np.array)
    """
    unit_ids = get_unit_ids_in_brain_region(patient_id, brain_region)
    spikes = []
    for i in unit_ids:
        spikes.append(get_spiking_activity(patient_id, session_nr, i))

    return spikes

def get_start_stop_times_pauses(patient_id, session_nr):
    """
    extract start and stop times of pauses from data base
    :param patient_id: patient ID (int)
    :param session_nr: session number (int)
    :return: two vectors, start and stop time points
    """
    start_times = (MoviePauses() & "patient_id={}".format(patient_id) & "session_nr={}".format(session_nr)).fetch("start_times")[0]
    stop_times = (MoviePauses() & "patient_id={}".format(patient_id) & "session_nr={}".format(session_nr)).fetch("stop_times")[0]
    
    return start_times, stop_times

def get_unit_id(csc_nr, unit_type, unit_nr, patient_id):
    """
    Returns the unit_id associated with a given spike train. 
    
    csc_nr: int, channel number from which the unit was recorded
    unit_type: char, type of unit (either M (multiple) or S (single))
    unit_nr: int, refers to the ordinal set of units (MUA 1, MUA 2) -- necessary 
                    as it is possible to sort several of the same unit type
                    from a given channel
    patient_id: int, patient id number
    
    output:
    unit_id: int, scalar id number specific to the patient and the unit 
    
    """
    unit_id = ((ElectrodeUnit & "csc = '{}'".format(csc_nr) & "patient_id = '{}'".format(patient_id)
             & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch('unit_id'))[0]
    
    return unit_id


def get_unit_ids_in_brain_region(patient_id, brain_region):
    """
    This function returns the unit IDs from within a certain brain region of a patient
    :param patient_id: patient ID (int)
    :param brain_region: brain region of interest - abbreviation (string)
    :return list of unit IDs (np.array)
    """
    name_vec = (ElectrodeUnit() & "patient_id={}".format(patient_id) & "brain_region='{}'".format(brain_region)).fetch("unit_id")
    
    return name_vec


def get_unit_level_data_cleaning(patient_id, session_nr, unit_id, name):
    """
    This function extracts a unit level cleaning vector from the database
    :param patient_id: patient ID (int)
    :param session_nr: session number of experiment (int)
    :param unit_id: ID of recorded unit (int)
    :param name: name of cleaning vector (string)
    :return extracted vector from database (np.array)
    """
    name_vec = ((UnitLevelDataCleaning() & "patient_id='{}'".format(patient_id) & "unit_id='{}'".format(unit_id) & "session_nr='{}'".format(session_nr) & "name='{}'".format(name)).fetch("data")[0])
    cleaning_vec = np.load(name_vec)
    if os.path.exists(name_vec):
        os.remove(name_vec)
    return cleaning_vec