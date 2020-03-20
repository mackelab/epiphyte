import datajoint as dj
import numpy as np
import os

import data_base.config as config
import data_base.helpers as helpers
import data_preprocessing.data_utils as data_utils

dhv_schema = dj.schema('dhv', locals())

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
    # general patient data
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
    # annatotors of the video
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
    # algorithms related to movie labels
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
                path_events = "{}/{}/session_{}/event_file/Events.nev".format(config.PATH_TO_PATIENT_DATA, patient_id,
                                                                              session_nr)

                time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                            path_to_events=path_events)
                pts, rectime, cpu_time = time_conversion.convert()

                cpu_time = cpu_time
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
    # names of existing labels
    label_name: varchar(32)   # label name
    """

    contents = config.label_names


@dhv_schema
class VideoAnnotation(dj.Imported):
    definition = """
    -> Annotator    # creator of movie annotation
    -> LabelName                           # name of annotation
    annotation_date: date   # date of annotation
    ---
    movie_label: attach     # frames with labeling
    category: varchar(32)   # category of label; e.g.: 'character', 'emotion', 'location'
    additional_information = "" : varchar(128)   # space for additional information
    """

    def _make_tuples(self, key):
        directory = "{}/movie_labels/".format(config.PATH_TO_DATA)
        print(directory)
        for filename in os.listdir(directory):
            if os.path.isfile(directory + filename) and filename.endswith(".npy"):
                label_id, name, annotator, date, category = filename[:-4].split("_")
                self.insert1({'label_name': name,
                              'annotator_id': annotator,
                              'movie_label': directory + filename,
                              'annotation_date': date[0:4] + "-" + date[4:6] + "-" + date[6:8],
                              'category': category
                              }, skip_duplicates=True)


@dhv_schema
class ElectrodeUnit(dj.Imported):
    definition = """
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
        for index_session in range(0, len(patient_ids)):
            channel_names = helpers.get_channel_names("ChannelNames.txt")
            path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_ids[index_session]) + '/session_' + str(
                session_nrs[index_session]) + "/"
            i = 0
            # iterate through all files in the binaries folder to see which units were recorded
            folder_list = []
            for filename in os.listdir(folder):
                if filename.startswith("CSC"):
                    folder_list.append(filename)
            folder_list.sort(key=helpers.natural_keys)

            for filename in folder_list:
                csc_nr, unit = filename[:-4].split("_")
                unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
                self.insert1({'unit_id': i, 'csc': csc_nr[3:], 'unit_type': unit_type, 'unit_nr': unit_nr,
                              'patient_id': patient_ids[index_session],
                              'brain_region': channel_names[int(csc_nr[3:]) - 1]},
                             skip_duplicates=True)
                i += 1
            # delete downloaded channel names file
            if os.path.exists("ChannelNames.txt"):
                os.remove("ChannelNames.txt")


@dhv_schema
class SpikeTimesDuringMovie(dj.Imported):
    definition = """
    -> ElectrodeUnit                # unit from which data was recorded
    -> MovieSession                 # session ID
    ---
    spike_times: attach              # in case bin_size is not 0: number of spikes; otherwise: times of spikes (original data)
    """

    def _make_tuples(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
        for index_session in range(0, len(patient_ids)):
            path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_ids[index_session]) + '/session_' + str(
                session_nrs[index_session]) + "/"
            if not os.path.exists(folder):
                os.makedirs(folder)
            # iterate through all files in the sessions folder and add them to the data base
            for filename in os.listdir(folder):
                if filename.startswith("CSC"):
                    csc_nr, unit = filename[:-4].split("_")
                    unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
                    spikes_file = (path_binaries + str(patient_ids[index_session]) + '/session_' + str(
                        session_nrs[index_session]) + "/" + filename)
                    # print("csc: {}, nr: {}, patient ID: {}, unit_type: {}".format(csc_nr, unit_nr, patient_id, unit_type))
                    unit_id = ((ElectrodeUnit & "csc = '{}'".format(csc_nr[3:]) & "patient_id='{}'".format(
                        patient_ids[index_session])
                                & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch(
                        "unit_id"))[0]
                    self.insert1({'patient_id': patient_ids[index_session], "unit_id": unit_id,
                                  'session_nr': session_nrs[index_session], 'spike_times': spikes_file},
                                 skip_duplicates=True)

                    print("Added spikes from {} of patient {} to data base".format(csc_nr + " " + unit,
                                                                                   patient_ids[index_session]))


@dhv_schema
class BinnedSpikesDuringMovie(dj.Imported):
    definition = """
    -> SpikeTimesDuringMovie
    bin_size: smallint                # size of bin in ms
    ---
    spike_vector: attach              # in case bin_size is not 0: number of spikes; otherwise: times of spikes (original data)
    """

    def _make_tuples(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
        for index_session in range(0, len(patient_ids)):
            path_binaries = '{}/spikes/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_ids[index_session]) + '/session_' + str(
                session_nrs[index_session]) + "/"
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
                        unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
                        unit_id = \
                            ((ElectrodeUnit & "csc = '{}'".format(csc_nr[3:]) & "patient_id='{}'".format(
                                patient_ids[index_session])
                              & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch("unit_id"))[
                                0]
                        spikes_file = (subfolder + "/" + filename)
                        self.insert1(
                            {'patient_id': patient_ids[index_session], 'bin_size': bin_size, 'unit_id': unit_id,
                             'session_nr': session_nrs[index_session], 'spike_vector': spikes_file},
                            skip_duplicates=True)
                        print("Added {} for binning {} of patient {} to data base".format(csc_nr + " " + unit,
                                                                                          bin_size,
                                                                                          patient_ids[index_session]))


@dhv_schema
class ProcessedVideoAnnotation(dj.Computed):
    definition = """
    -> LabelName
    -> LabelProcessingMethod
    last_entry_date: date    # date of most recent annotation entry
    ---
    processed_frames: longblob   # processed annotation on frames
    """

    class Entry(dj.Part):
        definition = """
        -> master
        -> VideoAnnotation
        """

    @property
    def key_source(self):
        # dj.U() is used to promote a non primary-key column into a primary key column
        return dj.U('last_entry_date') * (
                    LabelName.aggr(VideoAnnotation, last_entry_date='MAX(annotation_date)') * LabelProcessingMethod)

    def make(self, key):
        base_key = dict(key)  # make a copy for Part table entries
        if key['proc_method'] == 'method1':
            entry_keys, labeled_frames = (VideoAnnotation & key).fetch('KEY', 'labeled_frames')
            key['processed_frames'] = np.stack(labeled_frames).mean(axis=0)
            self.insert1(key)
            entry_keys = [dict(k, **base_key) for k in entry_keys]  # add master's columns into entry_keys
            self.Entry.insert(entry_keys)


@dhv_schema
class PatientAlignedLabel(dj.Computed):
    definition = """
    # Movie Annotations aligned to patient time
    -> VideoAnnotation     # label
    -> MovieSession        # movie watching session ID
    ---
    label_in_patient_time: longblob    # label matched to patient time (pts)
    """

    def make(self, key):
        entry_key_video_annot, original_label = (VideoAnnotation & key).fetch('KEY', 'movie_label')
        entry_key_movie_session, pts_vec = (MovieSession & key).fetch("KEY", 'order_movie_frames')
        patient_aligned_label = helpers.match_label_to_patient_pts_time(default_label=np.load(original_label[0]),
                                                                        patient_pts=np.load(pts_vec[0]))

        self.insert1({'annotator_id': entry_key_video_annot[0]['annotator_id'],
                      'label_name': entry_key_video_annot[0]['label_name'],
                      'annotation_date': entry_key_video_annot[0]['annotation_date'],
                      'patient_id': entry_key_movie_session[0]['patient_id'],
                      'session_nr': entry_key_movie_session[0]['session_nr'],
                      'label_in_patient_time': np.array(patient_aligned_label)}, skip_duplicates=True)


@dhv_schema
class BinnedPatientAlignedLabel(dj.Imported):
    definition = """
    # The patient aligned labels binned in certain milisecond bins
    -> VideoAnnotation     # label
    -> MovieSession        # movie watching session ID
    bin_size: smallint     # bin size in milliseconds
    ---
    label_in_patient_time: attach    # label matched to patient time (pts)
    """

    def _make_tuples(self, key):
        patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
        for index_session in range(0, len(patient_ids)):
            path_binaries = '{}/patient_aligned_labels/'.format(config.PATH_TO_DATA)
            folder = path_binaries + str(patient_ids[index_session]) + '/session_' + str(
                session_nrs[index_session]) + "/"
            if not os.path.exists(folder):
                os.makedirs(folder)
            # get all sub-folders in the folder, which contain the binned binaries
            sub_folders = [f.path for f in os.scandir(folder) if f.is_dir()]
            # iterate through sub-folders and add files to data base with respective bin sizes
            for subfolder in sub_folders:
                bin_size = subfolder.split("/")[-1]
                for filename in os.listdir(subfolder + "/"):
                    if filename.startswith("{}".format(patient_ids[index_session])):
                        patient_id, annotator_id, label_name, date = helpers.extract_binned_patient_aligned_label_information(filename)
                        label_file = (subfolder + "/" + filename)
                        self.insert1(
                            {'patient_id': patient_ids[index_session], 'bin_size': bin_size, 'annotator_id': annotator_id, 'annotation_date': date,
                             'session_nr': session_nrs[index_session], 'label_in_patient_time': label_file, 'label_name': label_name},
                            skip_duplicates=True)
                        print("Added binned label {} with bin size {} of patient {} to data base".format(label_name,
                                                                                          bin_size,
                                                                                          patient_ids[index_session]))


@dhv_schema
class UnitLevelDataCleaning(dj.Imported):
    definition = """
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


@dhv_schema
class PatientLevelDataCleaning(dj.Manual):
    definition = """
    -> MovieSession                    # number of movie session
    -> Annotator                       # who created the cleaning?
    name: varchar(16)                  # unique name for data cleaning
    ---
    data: attach                       # actual data
    description = "" : varchar(128)    # description of data cleaning
    """


@dhv_schema
class ContinuousWatchSegments(dj.Imported):
    definition = """
    -> MovieSession                    # number of movie session
    -> Annotator                       # who created the cleaning?
    label_entry_date: date             # date of creation of label
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
                    elif name == "smoothed4stddev":
                        description = "removing all bins where smoothed firing rate is greater than 4 std dev from mean"
                    else:
                        description = ""
                    self.insert1(
                        {'patient_id': patient_ids[index_session], "annotator_id": annotator,
                         'session_nr': session_nrs[index_session], "description": description, "name": name,
                         'data': "{}/{}".format(folder, filename)},
                        skip_duplicates=True)


@dhv_schema
class MoviePauses(dj.Computed):
    definition = """
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
            path_events = "{}/{}/session_{}/event_file/Events.nev".format(config.PATH_TO_PATIENT_DATA, patient_ids[i],
                                                                          session_nrs[i])

            time_conversion = data_utils.TimeConversion(path_to_wl=path_wl, path_to_dl=path_daq,
                                                        path_to_events=path_events)
            start, stop = time_conversion.convert_pauses()

            description = "time points of pauses, extracted from watch log - Mar 2020"

            self.insert1(
                {'patient_id': patient_ids[i], 'session_nr': session_nrs[i], "description": description,
                 'start_times': np.array(start), 'stop_times': np.array(stop)
                 },
                skip_duplicates=True)


def get_unit_id(csc_nr, unit_type, unit_nr, patient_id):
    return ((ElectrodeUnit & "csc = '{}'".format(csc_nr) & "patient_id = '{}'".format(patient_id)
             & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch('unit_id'))[0]


def get_brain_region(patient_id, unit_id):
    return (ElectrodeUnit & "patient_id='{}'".format(patient_id) & "unit_id='{}'".format(unit_id)).fetch('brain_region')[0]


def get_pts_of_patient(patient_id, session_nr):
    """
    Get the order of the movie in the way the patient watched it
    :param patient_id: ID of patient
    :param session_nr: number of movie watch session
    :return: vector of movie frames in the order the patient watched the movie
    """
    return np.load((MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch("order_movie_frames")[0])


def get_dts_of_patient(patient_id, session_nr):
    """
    Get dts of patient (cpu time), which is the time stamp matching the local time during the experiment
    :param patient_id: ID of patient
    :param session_nr: number of movie watch session
    :return: vector of cpu time that correspond to pts time stamps (extracted from watch log)
    """
    print("Note: Divide the patient dts vector by 1000 to get milliseconds")
    return np.load((MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch("cpu_time")[0])


def get_neural_rectime_of_patient(patient_id, session_nr):
    """
    Get neural recording time of patient
    :param patient_id: ID of patient
    :param session_nr: number of movie watch session
    :return: vector of neural recording time that correspond to pts time stamps
    """
    return np.load((MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch("neural_recording_time")[0])


def populate_all_tables():
    MovieSession.populate()
    VideoAnnotation.populate()
    ElectrodeUnit.populate()
    SpikeTimesDuringMovie.populate()
    BinnedSpikesDuringMovie.populate()
    ProcessedVideoAnnotation.populate()
    PatientAlignedLabel.populate()
    BinnedPatientAlignedLabel.populate()


def get_number_of_units_for_patient(patient_id):
    return ((Patient.aggr(ElectrodeUnit.proj(), number_of_units="count(*)")) & "patient_id='{}'"
            .format(patient_id)).fetch("number_of_units")[0]


def get_spiking_activity(patient_id, session_nr, bin_size, unit_id):
    """
    Extract spiking vector from data base. If bin_size is None, the spike times will be returned, otherwise the
    binned firing rates
    :param patient_id: ID of patient
    :param session_nr: session number
    :param bin_size: None or size of bin
    :param unit_id: Unit ID of which spiking activity shall be extracted
    """
    # if bin_size is None, return the spike times, otherwise return the binned firing rates
    if bin_size is None:
        try:
            spikes = (SpikeTimesDuringMovie & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(
                session_nr) & "unit_id='{}'".format(unit_id)).fetch("spike_times")[0]
        except:
            print("The spiking data you were looking for doesn't exist in the data base.")
            return -1
    else:
        try:
            spikes = (BinnedSpikesDuringMovie & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(
                session_nr) & "unit_id='{}'".format(unit_id) & "bin_size='{}'".format(bin_size)).fetch("spike_vector")[
                0]
        except:
            print("The spiking data you were looking for doesn't exist in the data base.")
            return -1

    spike_vec = np.load(spikes)

    if os.path.exists(spikes):
        os.remove(spikes)

    return spike_vec


def get_all_binned_spikes_of_patient(patient_id, session_nr, bin_size):
    """
    Returns a vector with all binned spikes for a patient, ordered by unit_id
    :param patient_id: int
    :param session_nr: int
    :param bin_size: int
    :return: sequence of all binned spikes
    """
    vec_binned_spikes = []
    for i in range(0, get_number_of_units_for_patient(patient_id)):
        binned_spikes = get_spiking_activity(patient_id=patient_id, session_nr=session_nr, bin_size=bin_size, unit_id=i)
        vec_binned_spikes.append(binned_spikes)
    return vec_binned_spikes


def get_all_binned_cleaned_spikes_of_patient(patient_id, session_nr, bin_size):
    """
    Returns a vector with all binned spikes for a patient, ordered by unit_id
    :param patient_id: int
    :param session_nr: int
    :param bin_size: int
    :return: sequence of all binned spikes after cleaning
    """
    vec_binned_spikes = []
    for i in range(0, get_number_of_units_for_patient(patient_id)):
        binned_spikes = get_spiking_activity(patient_id=patient_id, session_nr=session_nr, bin_size=bin_size, unit_id=i)
        vec_binned_spikes.append(binned_spikes)
    return vec_binned_spikes


def get_patient_aligned_label_simple_version(patient_id, label_name, session_nr):
    # this function doesn't check annotator ID or annotation date, so it's best to only use this one
    # if there is only one label with this name
    return (PatientAlignedLabel() & "label_name='{}'".format(label_name) & "patient_id='{}'".format(patient_id)
            & "session_nr='{}'".format(session_nr)).fetch("label_in_patient_time")[0]


def get_patient_aligned_label(patient_id, session_nr, label_name, annotator_id, annotation_date):
    """
    this function returns the patient aligned label with the respective parameters

    :param patient_id: patient ID (int)
    :param session_nr: session number (int)
    :param label_name: name of label (string)
    :param annotator_id: ID of annotator of label (string)
    :param annotation_date: date of creation of label (e.g. "2020-02-02")
    :return:
    """
    return (PatientAlignedLabel() & "label_name='{}'".format(label_name) & "patient_id='{}'".format(patient_id)
            & "session_nr='{}'".format(session_nr) & "annotator_id='{}'".format(annotator_id) &
            "annotation_date='{}'".format(annotation_date)).fetch("label_in_patient_time")[0]


def get_binned_patient_aligned_label(patient_id, session_nr, label_name, annotator_id, annotation_date, bin_size):
    name_binned_label = (BinnedPatientAlignedLabel() & "patient_id='{}'".format(patient_id) &
                         "label_name='{}'".format(label_name) & "bin_size='{}'".format(bin_size) &
                         "session_nr='{}'".format(session_nr) & "annotator_id='{}'".format(annotator_id)
                         & "annotation_date='{}'".format(annotation_date)).fetch("label_in_patient_time")[0]
    binned_label = np.load(name_binned_label)
    os.remove(name_binned_label)
    return binned_label


def get_unit_level_data_cleaning(patient_id, session_nr, unit_id, name):
    name_vec = ((UnitLevelDataCleaning() & "patient_id='{}'".format(patient_id) & "unit_id='{}'".format(unit_id) & "session_nr='{}'".format(session_nr) & "name='{}'".format(name)).fetch("data")[0])
    cleaning_vec = np.load(name_vec)
    if os.path.exists(name_vec):
        os.remove(name_vec)
    return cleaning_vec


def get_patient_level_data_cleaning(patient_id, session_nr, vector_name="continuous_pts"):
    name_pts_cont_watch = \
    (PatientLevelDataCleaning() & "name='{}'".format(vector_name) & "patient_id = '{}'".format(patient_id) & "session_nr='{}'".format(session_nr)).fetch("data")[0]
    cont_watch = np.load(name_pts_cont_watch)
    os.remove(name_pts_cont_watch)

    return cont_watch


def get_original_movie_label(label_name, annotation_date, annotator_id):
    name_label = (VideoAnnotation() & "label_name='{}'".format(label_name) & "annotator_id='{}'".format(annotator_id) & "annotation_date='{}'".format(annotation_date)).fetch("movie_label")[0]
    return np.load(name_label)


def get_all_patient_aligned_labels_of_patient(patient_id, session_nr):
    patient_aligned_label_information = (
                PatientAlignedLabel & "patient_id='{}'".format(patient_id) & "session_nr={}".format(session_nr)).proj(
        "annotator_id", "label_name", "annotation_date", "label_in_patient_time")

    return patient_aligned_label_information


def get_patient_level_cleaning_vec_from_db(patient_id, session_nr, name_of_vec, annotator_id):
    name_pts_cont_watch = (PatientLevelDataCleaning() & "name='{}'".format(name_of_vec)
                           & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(session_nr)
                           & "annotator_id='{}'".format(annotator_id)).fetch("data")[0]
    cont_watch = np.load(name_pts_cont_watch)
    return cont_watch


def get_movie_cutting_vec(patient_id, session_nr, bin_size):
    vorspann = get_binned_patient_aligned_label(patient_id, session_nr, "vorspann", "p5", "2020-02-21", bin_size)
    abspann = get_binned_patient_aligned_label(patient_id, session_nr, "abspann", "p5", "2020-02-21", bin_size)
    kidssegment = get_binned_patient_aligned_label(patient_id, session_nr, "kidssegment", "p5", "2020-02-21", bin_size)
    return vorspann + abspann + kidssegment


def get_movie_cutting_vec_excluding_pauses(patient_id, session_nr, bin_size):
    vorspann = get_patient_aligned_label(patient_id, session_nr, "vorspann", "p5", "2020-02-21")
    abspann = get_patient_aligned_label(patient_id, session_nr, "abspann", "p5", "2020-02-21")
    kidssegment = get_patient_aligned_label(patient_id, session_nr, "kidssegment", "p5", "2020-02-21")
    return vorspann + abspann + kidssegment


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


def get_spikes_from_brain_region(patient_id, session_nr, brain_region, bin_size):
    unit_ids = get_unit_ids_in_brain_region(patient_id, brain_region)
    spikes = []
    for i in unit_ids:
        spikes.append(get_spiking_activity(patient_id, session_nr, bin_size, i))

    return spikes


def get_unit_ids_in_brain_region(patient_id, brain_region):
    return (ElectrodeUnit() & "patient_id={}".format(patient_id) & "brain_region='{}'".format(brain_region)).fetch("unit_id")
