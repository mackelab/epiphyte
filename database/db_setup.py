import datajoint as dj
import numpy as np
import os

from datetime import datetime

import database.config as config
import database.helpers as helpers
from database.db_query_fxns import *

import preprocessing.data_preprocessing.data_utils as data_utils
import annotation.stimulus_driven_annotation.movies.processing_labels as processing_labels
import preprocessing.data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points

epi_schema = dj.schema('epiphyte_mock', locals())

dj.config['stores'] = {
    'local': {  # store in files
        'protocol': 'file',
        'location': os.path.abspath('./dj-store')
    }}

########################################################
# Table Definitions (in order of population procedure) #
########################################################

@epi_schema
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

@epi_schema
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

@epi_schema
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
        for pat_dir in os.listdir(config.PATH_TO_PATIENT_DATA):
            print(pat_dir)
            for session_dir in os.listdir(os.path.join(config.PATH_TO_PATIENT_DATA, pat_dir)):
                print(session_dir)

                try:
                    print("Checking if patient is already uploaded..")
                    check = (MovieSession & "patient_id='{}'".format(pat_dir) & "session_nr='{}'".format(session_dir)).fetch("date")
                    if len(check) > 0:
                        print("Patient {}, session {} already in database. Continuing on..".format(pat_dir, session_dir))
                        continue
                    else:
                        print("Adding {}, session {} to database..".format(pat_dir, session_dir))
                        pass
                except:
                    print("Adding {}, session {} to database..".format(pat_dir, session_dir))
                    pass

                for content in os.listdir(os.path.join(config.PATH_TO_PATIENT_DATA, pat_dir, session_dir)):
                    print(content)
                    if content.startswith("session_info"):

                        session_info = np.load(os.path.join(config.PATH_TO_PATIENT_DATA, pat_dir, session_dir, content), allow_pickle=True)

                        patient_id = session_info.item().get("pat_id")
                        session_nr = session_info.item().get("session_nr")
                        date = session_info.item().get("date")
                        time = session_info.item().get("time")

                        main_patient_dir = os.path.join(config.PATH_TO_PATIENT_DATA, str(int(patient_id)), "session_{}".format(session_nr))
                        print(main_patient_dir)

                        path_wl = os.path.join(main_patient_dir, "watchlogs", config.watchlog_names[patient_id])
                        path_daq = os.path.join(main_patient_dir, "daq_files", config.daq_names[patient_id])

                        for file in os.listdir(os.path.join(main_patient_dir, "event_file")):
                            if file.startswith("Events"):
                                path_events = os.path.join(main_patient_dir, "event_file", file)

                        time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                                    path_to_events=path_events)
                        pts, rectime, cpu_time = time_conversion.convert()

                        cpu_time = cpu_time

                        save_dir = os.path.join(main_patient_dir, "order_of_movie_frames")


                        if not os.path.exists(save_dir):
                            os.makedirs(save_dir)

                        path_order_movie_frames = os.path.join(save_dir, "pts.npy")

                        np.save(path_order_movie_frames, pts)
                        path_cpu_time = os.path.join(save_dir, "dts.npy")

                        np.save(path_cpu_time, cpu_time)
                        path_neural_rectime = os.path.join(save_dir, "neural_rec_time.npy")

                        np.save(path_neural_rectime, rectime)
                        path_channel_names = os.path.join(main_patient_dir, "ChannelNames.txt")


                        self.insert1({'patient_id': patient_id,
                                      'session_nr': session_nr,
                                      'date': date,
                                      'time': time,
                                      'order_movie_frames': path_order_movie_frames,
                                      'cpu_time': path_cpu_time,
                                      'neural_recording_time': path_neural_rectime,
                                      'channel_names': path_channel_names
                                      }, skip_duplicates=True)

@epi_schema
class ElectrodeUnit(dj.Imported):
    definition = """
    # Contains information about the implanted electrodes of each patient
    session_nr: int                  # session ID
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
        print("Patients in database: {}".format(patient_ids))

        # iterate over each patient in db
        for i_pat, pat in enumerate(patient_ids):
            pat_sessions = session_nrs[i_pat]
            # further iterate over each patient's sessions
            for i_sesh, sesh in enumerate([pat_sessions]):
                print("Patient ID: {}, Session: {}".format(pat, sesh))

                try:
                    check = (ElectrodeUnit & "patient_id='{}'".format(pat) & "session_nr='{}'".format(sesh) & "unit_id='{}'".format(0)).fetch("brain_region")
                    if len(check) > 0:
                        continue
                    else:
                        print("Adding {}, session {} to database..".format(pat, sesh))
                        pass
                except:
                    print("Adding {}, session {} to database..".format(pat, sesh))
                    pass

                path_binaries = config.PATH_TO_PATIENT_DATA
                path_channels = os.path.join(config.PATH_TO_PATIENT_DATA, str(pat), "session_{}".format(sesh))

                channel_names = helpers.get_channel_names(os.path.join(path_channels, "ChannelNames.txt"))

                # iterate through all files in the binaries folder to see which units were recorded
                folder_list = []

                dir_w_dir = os.path.join(config.PATH_TO_DATA, "patient_data", str(pat), "session_{}".format(sesh))

                folder_spikes_nm = []
                for folder in os.listdir(dir_w_dir):
                    if folder.startswith("spik"):
                        # accounting for differences in file structure btw mock and real data
                        folder_spikes_nm.append(folder)

                dir_w_spikes = os.path.join(config.PATH_TO_DATA, "patient_data", str(pat), "session_{}".format(sesh), folder_spikes_nm[0])

                for filename in os.listdir(dir_w_spikes):
                    if filename.startswith("CSC"):
                        folder_list.append(filename)

                folder_list.sort(key=helpers.natural_keys)

                for index, filename in enumerate(folder_list):
                    csc_nr, unit = filename[:-4].split("_")
                    csc_index = int(csc_nr[3:]) - 1
                    print(csc_nr, csc_index)

                    # match channel to unit csc
                    channel = channel_names[csc_index]
                    print("Channel: ", channel)

                    unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
                    print("Unit type: {},  Unit Number: {}".format(unit_type, unit_nr))
                    print("Unit ID: {}".format(index))
                    print("")
                    self.insert1({'unit_id': index, 'csc': csc_nr[3:], 'unit_type': unit_type, 'unit_nr': unit_nr,
                                  'patient_id': pat,
                                  'session_nr': sesh,
                                  'brain_region': channel},
                                 skip_duplicates=True)

@epi_schema
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
            try:
                check = (SpikeTimesDuringMovie & "patient_id='{}'".format(patient_ids[index_session]) & "session_nr='{}'".format(1) & "unit_id='{}'".format(0)).fetch("spike_times")
                if len(check) > 0:
                    print("Patient {}, session {} already in database. Continuing on..".format(patient_ids[index_session], 1))
                    continue
                else:
                    print("Adding {}, session {} to database..".format(patient_ids[index_session], 1))
                    pass
            except:
                print("Adding {}, session {} to database..".format(patient_ids[index_session], 1))
                pass

            
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

@epi_schema
class LabelProcessingMethod(dj.Lookup):
    definition = """
    # algorithms related to movie annotations
    algorithm_name: varchar(16)                     # unique name for each algorithm
    ---
    description: varchar(128)                    # description of algorithm
    """
    contents = config.algorithms_labels

@epi_schema
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

                ind_func = processing_labels.make_label_from_start_stop_times(values, start_times, stop_times,
                                                                              config.PTS_MOVIE_new)

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

@epi_schema
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

@epi_schema
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

        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")

        entries_og = (MovieAnnotation).fetch('KEY')

        for i_pat, pat in enumerate(patient_ids):
            pat_sessions = session_nrs[i_pat]

            if pat == 12:
                continue

            for i_sesh, sesh in enumerate([pat_sessions]):
                print("Patient ID: {}, Session: {}".format(pat, sesh))
                try:
                    check = (PatientAlignedMovieAnnotation & "patient_id='{}'".format(pat) & "session_nr='{}'".format(sesh)).fetch(
                        "brain_region")
                    if len(check) > 0:
                        continue
                    else:
                        print("Adding {}, session {} to database..".format(pat, sesh))
                        pass
                except:
                    print("Adding {}, session {} to database..".format(pat, sesh))
                    pass

                ## Load in patient information
                # pull patient information corresponding to the watchlog
                patient_pts = get_pts_of_patient(pat, sesh)

                # pull the timestamps corresponding to frame presentation
                neural_rec_time = get_neural_rectime_of_patient(pat, sesh)

                for i_label, label in enumerate(entries_og):

                    label_name = label["label_name"]
                    annotation_date = label["annotation_date"]
                    annotator_id = label["annotator_id"]

                    print("...aligning label {}".format(label_name))

                    # pull "raw" label of the movie
                    default_label = get_original_movie_label(label_name, annotation_date, annotator_id)

                    # match the "raw" label to the patient watchlog, creating patient aligned label
                    patient_aligned_label = helpers.match_label_to_patient_pts_time(default_label, patient_pts)

                    # find the timestamps in neural rec time associated with the aligned label
                    values, starts, stops = create_vectors_from_time_points.get_start_stop_times_from_label(neural_rec_time,
                                                                                            patient_aligned_label)


                    self.insert1({'patient_id': pat,
                          'session_nr': sesh,
                          'annotator_id': annotator_id,
                          'label_name': label_name,
                          'annotation_date': annotation_date,
                          'label_in_patient_time': np.array(patient_aligned_label),
                          'values': np.array(values),
                          'start_times': np.array(starts),
                          'stop_times': np.array(stops),
                         }, skip_duplicates=True)

                    print("...added to db!")

@epi_schema
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
        print("Patients in database: {}".format(patient_ids))

        # iterate over each patient in db
        for i_pat, pat in enumerate(patient_ids):
            pat_sessions = session_nrs[i_pat]
            # further iterate over each patient's sessions
            for i_sesh, sesh in enumerate([pat_sessions]):
                print("Patient ID: {}, Session: {}".format(pat, sesh))

                main_patient_dir = os.path.join(config.PATH_TO_PATIENT_DATA, str(int(pat)), "session_{}".format(sesh))

                ### testing -- workaround for difference in file name format
                session_info = np.load(os.path.join(main_patient_dir, "session_info.npy"), allow_pickle=True)

                patient_id = session_info.item().get("pat_id")
                session_nr = session_info.item().get("session_nr")
                date = session_info.item().get("date")
                time = session_info.item().get("time")
                ###

                print("Calculating and adding movie skips for patient {} session {}..".format(pat, sesh))

                path_wl = os.path.join(main_patient_dir, "watchlogs", config.watchlog_names[pat])
                path_daq = os.path.join(main_patient_dir, "daq_files", config.daq_names[pat])

                for file in os.listdir(os.path.join(main_patient_dir, "event_file")):
                    if file.startswith("Events"):
                        path_events = os.path.join(main_patient_dir, "event_file", file)
            
                time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                        path_to_events=path_events)
            
                starts, stops, values = time_conversion.convert_skips()

            ###### hacky fix for the interactive plot 
            ##### TODO: get pausing time stamps to align in magnitude 

                notes = "time points of continuous watch, extracted from watch log - {}".format(datetime.today())
             
                self.insert1(
                    {'patient_id': int(pat), 'session_nr': sesh, "notes": notes,
                     'start_times': np.array(starts), 'stop_times': np.array(stops), 'values': np.array(values)
                     },
                    skip_duplicates=True)
            

@epi_schema
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


            # the following if conditions account for
            # the fact that some patients may have only a
            # single session, and some a multiple.
            if isinstance(session_nrs[i], np.int64):
                patient = patient_ids[i]
                session = session_nrs[i]
                print("Patient has a single session.")

            if not isinstance(session_nrs[i], np.int64):
                for j in range(len(session_nrs[i])):
                    patient = patient_ids[i]
                    session = j
                    print("Patient has multiple sessions.")

            main_patient_dir = os.path.join(config.PATH_TO_PATIENT_DATA, str(int(patient_ids[i])), "session_{}".format(session))

            ### testing -- workaround for difference in file name format
            session_info = np.load(os.path.join(main_patient_dir, "session_info.npy"), allow_pickle=True)

            patient_id = session_info.item().get("pat_id")
            session_nr = session_info.item().get("session_nr")
            date = session_info.item().get("date")
            time = session_info.item().get("time")
            ###

            path_wl = os.path.join(main_patient_dir, "watchlogs", config.watchlog_names[patient_id])
            path_daq = os.path.join(main_patient_dir, "daq_files", config.daq_names[patient_id])

            for file in os.listdir(os.path.join(main_patient_dir, "event_file")):
                if file.startswith("Events"):
                    path_events = os.path.join(main_patient_dir, "event_file", file)

            time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                        path_to_events=path_events)
            start, stop = time_conversion.convert_pauses()

            description = "time points of pauses, extracted from watch log - {}".format(datetime.today())

            self.insert1(
                {'patient_id': int(patient_id), 'session_nr': session_nr, "description": description,
                 'start_times': np.array(start), 'stop_times': np.array(stop)
                 },
                skip_duplicates=True)

@epi_schema
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

@epi_schema
class LabelName(dj.Lookup):
    definition = """
    # names of existing labels, imported from config file
    label_name: varchar(32)   # label name
    """

    contents = config.label_names

@epi_schema
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
