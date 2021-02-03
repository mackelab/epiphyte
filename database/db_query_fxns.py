# Functions for database queries and common database manipulations

# to use these in a file, add the following to the imports:
# from database.db_query_fxns import *

import datajoint as dj
import numpy as np
import pandas as pd
import os

from database.db_setup import *

def get_brain_region(patient_id, session_nr, unit_id):
    """
    Returns the brain region of a given unit for a given patient.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        unit_id: int, unit id number

    Returns: str, brain region associated with the unit

    """
    region = (ElectrodeUnit & "patient_id='{}'".format(patient_id) & "session_nr={}".format(session_nr)
              & "unit_id='{}'".format(unit_id)).fetch('brain_region')[0]

    return region


def get_cscs_for_patient(patient_id, session_nr):
    """
    For a given patient/session, returns a list of csc's.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        array-like: csc ids for a given patient + session

    """
    vec = (ElectrodeUnit & "patient_id={}".format(patient_id)
           & "session_nr={}".format(session_nr)).fetch("csc")
    ret = np.unique(vec)

    return ret

def get_date_and_time_session(patient_id, session_nr):
    """
    Get the data and time of an experimental session.

    Args:
          patient_id (int): patient id number
          session_nr (int): session id number
    Returns:                                               
       array-like: date object, time object
    """
    date, time = (MovieSession & "patient_id={}".format(patient_id) & "session_nr='{}'".format(session_nr)).fetch("date", "time")

    date = date[0]
    time = time[0]

    return date, time


def get_dts_of_patient(patient_id, session_nr):
    """
    Get dts of patient (cpu time), which is the time stamp matching the local time during the experiment
    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
         vector of cpu time that correspond to pts time stamps (extracted from watch log)
    """
    print("Note: Divide the patient dts vector by 1000 to get milliseconds")

    name_vec = (MovieSession & "patient_id={}".format(patient_id)
                & "session_nr='{}'".format(session_nr)).fetch("cpu_time")[0]

    dts = np.load(name_vec)

    if os.path.exists(name_vec):
        os.remove(name_vec)

    return dts


def get_first_last_spikes(patient_id, session_nr):
    """
    Calculates and returns the time of the first and the last spike in neural
    rec time for a whole patient session recording.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        global_min (float): first spike time in the session
        global_max (float): last spike time in the session
    """
    list_min = []
    list_max = []

    units = get_unit_ids_for_patient(patient_id, session_nr)

    for unit in units:
        load = get_spiking_activity(patient_id, session_nr, unit)

        list_min.append(np.min(load))
        list_max.append(np.max(load))

    global_min = np.min(list_min)
    global_max = np.max(list_max)

    return global_min, global_max

def get_info_continuous_watch_segments(patient_id, session_nr):
    """
    This function returns the start times, stop times and values of the continuous watch segment
    From these, it's possible to reconstruct a vector representing the whole continuous
    portions of the watch session.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        values (array-like): index of continuous segments
        starts (array-like): onsets of each continuous segments, in neural rec time
        stops (array-like): offsets of each continuous segments, in neural rec time
    """
    values, starts, stops = (MovieSkips & "patient_id={}".format(patient_id)
                             & "session_nr={}".format(session_nr)).fetch('values', 'start_times', 'stop_times')
    return values[0], starts[0], stops[0]


def get_neural_rectime_of_patient(patient_id, session_nr):
    """
    Get the neural recording time of patient during the movie playback.
    Use as a look-up between frames and neural spike times.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        vector of timestamps corresponding the the pts timestamps (frames).
    """
    name_vec = (MovieSession & "patient_id={}".format(patient_id)
                             & "session_nr={}".format(session_nr)).fetch("neural_recording_time")[0]

    rectime = np.load(name_vec)

    if os.path.exists(name_vec):
        os.remove(name_vec)

    return rectime


def get_number_of_units_for_patient(patient_id, session_nr):
    """
    returns the number of recorded units from a patient
    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        number of recorded units
    """
    name_vec = ((Patient.aggr(ElectrodeUnit.proj(), number_of_units="count(*)"))
                & "patient_id='{}'".format(patient_id) & "session_nr={}".format(session_nr)).fetch(
        "number_of_units")[0]

    return name_vec


def get_original_movie_label(label_name, annotation_date, annotator_id):
    """
    Returns the original movie label from the database

    Args:
        label_name (str): name of the label
        annotation_date (datetime): date of annotation
        annotator_id (str): ID of annotator

    Returns:
    extracted vector from database (np.array)
    """
    name_vec = (MovieAnnotation() & "label_name='{}'".format(label_name) & "annotator_id='{}'".format(
        annotator_id) & "annotation_date='{}'".format(annotation_date)).fetch("indicator_function")[0]

    return name_vec


def get_patient_aligned_annotations(patient_id, label_name, annotator_id, annotation_date):
    """
    Returns the values, starts, and stop times of a given label as tailored to the
    watchlog of a specific patient.

    Args:
        patient_id (int): patient id number
        label_name (str): name of the label
        annotator_id (str): ID of annotator
        annotation_date (datetime): date of annotation

    Returns:
        values (array-like): list of 1's and 0's  (1 is label applies to the segment of time, 0 otherwise)
        starts (array-like): onsets of segments, in neural rec time
        stops (array-like): offsets of segments, in neural rec time
    """
    values, starts, stops = (
                PatientAlignedMovieAnnotation() & "label_name='{}'".format(label_name) & "annotator_id='{}'".format(
            annotator_id) & "annotation_date='{}'".format(annotation_date) & "patient_id='{}'".format(
            patient_id)).fetch("values", "start_times", "stop_times")

    values = values[0]
    starts = starts[0] / 1000
    stops = stops[0] / 1000

    return values, starts, stops


def get_pts_of_patient(patient_id, session_nr):
    """
    Get the order of the movie frames corresponding the the patient's watchlog.
    Note: since a patient can freely pause and move around in the movie, the resulting
    vector is not by necessity monotonic.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        vector of movie frames in the order the patient watched the movie
    """
    name_vec = (MovieSession & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(session_nr)).fetch(
        "order_movie_frames")[0]
    pts = np.load(name_vec)

    if os.path.exists(name_vec):
        os.remove(name_vec)

    return pts


def get_scr_eventtimes(patient_id, session_nr):
    """
    For a given patient/session, returns the order of stimuli presentation and corresponding
    eventtimes in neural recording time (dts).

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        stim_index (array-like): index of the images shown, corresponds to image names
        time (array-like): time in neural rec time when the corresponding stim_index image was shown
    """
    stim_index, time = (ScreeningAnnotation & "patient_id={}".format(patient_id)
                        & "session_nr={}".format(session_nr)).fetch("stim_index", "time")

    return stim_index, time


def get_scr_stats_as_df(patient_id, session_nr, unit_id):
    """
    Pulls the screening-related stats (active trials, various p-values) for a given unit from a given patient
    session and outputs them as a Pandas dataframe.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        unit_id (int): unit id number

    Returns:
        pandas dataframe containing the unit's screening information
    """
    position, stim_id, active_trials, pval_scr, pval_bwscr = (ScreeningStats & "patient_id={}".format(patient_id)
                                                              & "session_nr={}".format(
                session_nr) & "unit_id={}".format(unit_id)).fetch("position", "stim_id", "active_trials", "pval_scr",
                                                                  "pval_bwscr")
    names = []
    for stim in stim_id:
        names.append(get_stimulus_name(stim))

    pre_frame = OrderedDict()
    pre_frame['position'] = position
    pre_frame['stim_num'] = stim_id
    pre_frame['stim_name'] = names
    pre_frame['active_trials'] = active_trials
    pre_frame['pval_scr'] = pval_scr
    pre_frame['pval_bwsr'] = pval_bwscr

    return pd.DataFrame(pre_frame)


def get_session_info(patient_id):
    """
    For a specific patient, get the session information.

    Args:
        patient_id (int): patient id number

    Returns:
        (array-like) session ids for a given patient
    """
    sessions = (MovieSession & "patient_id={}".format(patient_id)).fetch("session_nr")

    if len(sessions) == 1:
        ret = int(sessions[0])
    else:
        ret = sessions

    return ret


def get_screening_data(patient_id, session_nr):
    """
    Get screening experiment information for a given patient's session.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        position (array): for each stimulus seen by the patient, whether it was 'pre' movie or 'post' movie
        stim_id (array): stimulus image id number
        filename (array): filename of each shown image
        stim_name (array): stimulus name of each shown image
        is_500_days (array): True if stimulus is taken from 500days movie, False otherwise
        time (array): time when stimulus was presented in neural rec time (milliseconds)
    """
    position, stim_id, filename, stim_name, is_500_days, paradigm, time = (
                ScreeningAnnotation & "patient_id = '" + str(patient_id) + "'" & "session_nr='{}'".format(
            session_nr)).fetch("position", "stim_id", "filename", "stim_name", "is_500_days", "paradigm", "time")

    return position, stim_id, filename, stim_name, is_500_days, paradigm, time


def get_sig_scr_images_by_unit(patient_id, session_nr, unit_id, alpha=0.05):
    """
    Retrieves the stimulus ids/information for stimuli which elicited a
    significant change in firing rate for a given unit.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        unit_id (int): unit id number
        alpha (float):  significance threshold by which stimulus/unit pairs are filtered

    Returns:
        position: for a given result, whether it is from the pre or post movie screening
        stim_id: id number of the stimulus
        pval_scr: pvalue for the screening, fmormann calc
        pval_bwscr: pvalue for the binwise screening, signed rank sum
    """
    position, stim_id, pval_scr, pval_bwscr = (ScreeningStats & "patient_id={}".format(patient_id) &
                                               "session_nr={}".format(session_nr) & "unit_id={}".format(unit_id)
                                               & "pval_scr <= {}".format(alpha)).fetch("position", "stim_id",
                                                                                       "pval_scr", "pval_bwscr")

    return position, stim_id, pval_scr, pval_bwscr

def get_spikes_from_brain_region(patient_id, session_nr, brain_region):
    """
    Extracts all spiking vectors from a specific brain region.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        brain_region (str): brain region to pull spikes from

    Returns:
        (array-like): unit activity vectors from the region in question
    """
    unit_ids = get_unit_ids_in_brain_region(patient_id, brain_region)
    spikes = []
    for i in unit_ids:
        spikes.append(get_spiking_activity(patient_id, session_nr, i))

    return spikes


def get_spikes_from_patient_session(patient_id, session_nr):
    """
    Returns an array of size (total_units, 1) containing all the spike trains from a given patient for a
    given session.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        (array-like): all spiking unit vectors for a given patient's session
    """

    unit_ids = get_unit_ids_for_patient(patient_id, session_nr)

    spikes = []
    for i in unit_ids:
        spikes.append(get_spiking_activity(patient_id, session_nr, i))

    return spikes

def get_spiking_activity(patient_id, session_nr, unit_id):
    """
    Extract spiking vector from data base.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        unit_id (int): unit id number

    Returns:
        (array-like) vector containing all the spike times
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


def get_start_stop_times_pauses(patient_id, session_nr):
    """
    Extracts start and stop times of pauses from data base.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        start_times (array-like): onsets of pauses in the watchlog, neural rec time
        stop_times (array-like): offsets of pauses in the watchlog, neural rec time
    """
    start_times = (MoviePauses & "patient_id={}".format(patient_id)
                   & "session_nr={}".format(session_nr)).fetch("start_times")[0]
    stop_times = (MoviePauses & "patient_id={}".format(patient_id)
                  & "session_nr={}".format(session_nr)).fetch("stop_times")[0]

    return start_times, stop_times


def get_stimulus_name(stim_id):
    """
    Get stimulus name based on the id number.

    Args:
        stim_id (int):  id number for the stimulus

    Returns:
        (str): name of the stimulus
    """
    patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")
    patient = patient_ids[0]
    session = session_nrs[0]

    name = (ScreeningAnnotation & "patient_id={}".format(patient) & "session_nr={}".format(session)
            & "position='{}'".format("pre") & "stim_id={}".format(stim_id)).fetch("stim_name")[0]

    return name


def get_unit_id(csc_nr, unit_type, unit_nr, patient_id):
    """
    Returns the unit_id associated with a given spike train.

    Args:
        csc_nr (int): continuous sampling channel number from which the unit was recorded
        unit_type (char): either M (multiple) or S (single)
        unit_nr (int): order of the unit wrt unit type (e.g., 1 if unit is the 1st single unit clustered)
        patient_id (int): patient id number

    Returns:
        (int) unit id in the database
    """
    unit_id = ((ElectrodeUnit & "csc = '{}'".format(csc_nr) & "patient_id = '{}'".format(patient_id)
                & "unit_type='{}'".format(unit_type) & "unit_nr='{}'".format(unit_nr)).fetch('unit_id'))[0]

    return unit_id


def get_unit_ids_in_channel(patient_id, session_nr, csc):
    """
    Returns the unit ids from within a given csc electrode.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        csc (int): csc electrode to pull from

    Returns:
        (array-like): list of unit ids for spike trains clustered from the given channel
    """
    name_vec = (ElectrodeUnit() & "patient_id={}".format(patient_id) & "session_nr={}".format(session_nr)
                & "csc={}".format(csc)).fetch("unit_id")

    return name_vec


def get_unit_ids_for_patient(patient_id, session_nr):
    """
    Returns a list of all unit ids for a given patient and session.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number

    Returns:
        (array-like) list of all unit ids for the patient and session
    """
    name_vec = (ElectrodeUnit() & "patient_id={}".format(patient_id)
                & "session_nr={}".format(session_nr)).fetch(
        "unit_id")

    return name_vec


def get_unit_ids_in_brain_region(patient_id, session_nr, brain_region):
    """
    Returns the unit ids from within a certain brain region of a patient/session.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        brain_region (str): region of interest in the brain

    Returns:
        (array-like): unit ids within the given region for the given patient and session
    """
    name_vec = (ElectrodeUnit() & "patient_id={}".format(patient_id) & "session_nr={}".format(session_nr)
                & "brain_region='{}'".format(brain_region)).fetch("unit_id")

    return name_vec

def get_unit_level_data_cleaning(patient_id, session_nr, unit_id, name):
    """
    Extracts a unit level cleaning vector from the database.

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        unit_id (int): unit id number
        name (str): name of the cleaning method

    Returns:
        (array-like) cleaning vector
    """
    name_vec = ((UnitLevelDataCleaning() & "patient_id='{}'".format(patient_id) & "unit_id='{}'".format(unit_id) & "session_nr='{}'".format(session_nr) & "name='{}'".format(name)).fetch("data")[0])
    cleaning_vec = np.load(name_vec)
    if os.path.exists(name_vec):
        os.remove(name_vec)
    return cleaning_vec


def get_unit_type(patient_id, session_nr, unit_id):
    """
    Get the cluster type of a unit (either single or multi).

    Args:
        patient_id (int): patient id number
        session_nr (int): session id number
        unit_id (int): unit id number

    Returns:
        (tuple): cluster type
    """
    name_vec = (ElectrodeUnit & "patient_id='{}'".format(patient_id) & "session_nr='{}'".format(
        session_nr) & "unit_id='{}'".format(unit_id)).fetch('unit_type')[0]

    return name_vec

