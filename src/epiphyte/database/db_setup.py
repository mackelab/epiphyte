"""Table classes and population functions (skeleton of the database)"""

import os
from pathlib import Path
from datetime import datetime

import datajoint as dj
import numpy as np

from .access_info import *
from . import config, helpers

from ..preprocessing.data_preprocessing import data_utils
from ..preprocessing.annotation.stimulus_driven_annotation.movies import processing_labels


########################################################
# Table Definitions (in order of population procedure) #
########################################################

@epi_schema
class Patients(dj.Lookup):
    definition = """
    # general patient data, imported from config file
    patient_id: int                                    # patient ID
    ---
    age: smallint                                      # age of patient
    gender: enum('f', 'm', 'x')                        # gender of patient
    year: int                                          # year of surgery
    """

    contents = config.patients

@epi_schema
class Sessions(dj.Lookup):
    definition = """
    # general session data, imported from config file
    patient_id: int                                    # patient ID
    session_nr: int                                    # session number
    ---
    session_type: enum('full_movie', 'follow_up', 'partial_movie')   # type of session for corresponding recording
    """

    contents = config.sessions

@epi_schema
class Annotator(dj.Lookup):
    definition = """
    # annatotors of the video, imported from config file
    annotator_id: varchar(5)                    # unique ID for each annotator
    ---
    first_name: varchar(32)                      # first name of annotator
    last_name: varchar(32)                       # last name of annotator
    """

    contents = config.annotators

@epi_schema
class LabelName(dj.Lookup):
    definition = """
    # names of existing labels, imported from config file
    label_name: varchar(32)   # label name
    """

    contents = config.label_names

@epi_schema
class MovieSession(dj.Imported):
    definition = """
    # data of individual movie watching sessions
    -> Patients                          # patient ID
    -> Sessions                          # session ID
    ---
    date : date                         # date of movie session
    time : time
    pts: longblob                       # order of movie frames for patient (pts) 
    dts: longblob                       # cpu time stamps (dts)
    neural_recording_time: longblob     # neural recording time (rectime)
    channel_names: longblob             # channel name, indicating electrode number and brain region
    """
    
    def _make_tuples(self, key):
        patient_ids = Patients.fetch("patient_id")       

        for _, pat in enumerate(patient_ids):

            pat_sessions = (Sessions & f"patient_id={pat}").fetch("session_nr")       

            try:
                checks = (MovieSession & f"patient_id={pat}").fetch("session_nr")
                if len(checks) == len(pat_sessions):
                    print(checks)
                    print(len(checks), len(pat_sessions))
                    continue
                else:
                    print(f"Adding patient {pat} to database...")
                    pass
            except:
                print(f"Adding patient {pat} to database...")
                pass

            for _, sesh in enumerate(pat_sessions):

                try:
                    check = len((MovieSession & f"patient_id={1}" & f"session_nr={1}").fetch("pts")[0])
                    if check > 0:
                        print(f"Adding patient {pat} to database...")
                        pass
                    else:
                        continue
                except:
                    print(f"Adding patient {pat} to database...")
                    pass

                main_patient_dir = Path(config.PATH_TO_PATIENT_DATA, str(pat), f"session_{sesh}")

                session_info = np.load(main_patient_dir / "session_info.npy", allow_pickle=True)
                date = session_info.item().get("date")
                time = session_info.item().get("time")
                time = datetime.strptime(time, '%H-%M-%S').strftime('%H:%M.%S')

                path_wl =  main_patient_dir / "watchlogs" 
                ffplay_file = next(path_wl.glob("ffplay*"), None)

                if ffplay_file:
                    print(" Found ffplay file:", ffplay_file)
                else:
                    print(" No ffplay file found in the watchlogs directory.")
                    break

                path_daq = main_patient_dir / "daq_files" 
                daq_file = next(path_daq.glob("timedDAQ*"), None)
                
                if ffplay_file:
                    print(" Found DAQ file:", daq_file)
                else:
                    print(" No DAQ file found in the daq_files directory.")
                    break
                    
                path_events = main_patient_dir / "event_file" / "Events.npy"
                time_conversion = data_utils.TimeConversion(path_to_wl=ffplay_file, path_to_dl=daq_file,
                                                                    path_to_events=path_events)
                pts, rectime, dts = time_conversion.convert()
                
                save_dir = main_patient_dir / "movie_info"
                save_dir.mkdir(exist_ok=True)
                np.save(save_dir / "pts.npy", pts)
                np.save(save_dir / "dts.npy", dts)
                np.save(save_dir / "neural_rec_time.npy", rectime)

                path_channel_names = main_patient_dir / "ChannelNames.txt"
                channel_names = helpers.get_channel_names(path_channel_names)

                self.insert1({'patient_id': pat,
                            'session_nr': sesh,
                            'date': date,
                            'time': time,
                            'pts': pts,
                            'dts': dts,
                            'neural_recording_time': rectime,
                            'channel_names': channel_names
                            }, skip_duplicates=True)
                
@epi_schema
class ElectrodeUnit(dj.Imported):
    definition = """
    # Contains information about the implanted electrodes of each patient
    -> Patients                      # patient ID
    -> Sessions                      # session number
    unit_id: int                     # unique ID for unit (for respective  patient)
    ---
    csc: int                         # number of CSC file
    unit_type: enum('M', 'S', 'X')   # unit type: 'M' for Multi Unit, 'S' for Single Unit, 'X': undefined
    unit_nr: int                     # number of unit, as there can be several multi units and single units in one CSC file
    brain_region: varchar(8)         # brain region where unit was recorded
    """

    def _make_tuples(self, key):
        patient_ids = Patients.fetch("patient_id")

        # iterate over each patient in db
        for i_pat, pat in enumerate(patient_ids):
            pat_sessions = (Sessions & f"patient_id={pat}").fetch("session_nr")

            # further iterate over each patient's sessions
            for i_sesh, sesh in enumerate(pat_sessions):

                path_binaries = config.PATH_TO_PATIENT_DATA
                path_channels = Path(config.PATH_TO_PATIENT_DATA, str(pat), f"session_{sesh}")
                channel_names = helpers.get_channel_names(path_channels / "ChannelNames.txt")

                try:
                    check = (ElectrodeUnit & f"patient_id={pat}" & f"session_nr={sesh}").fetch("csc_nr")
                    if len(check) == len(channel_names):
                        continue
                    else:
                        print(f"    Adding patient {pat} session {sesh} to database...")
                        pass
                except:
                    print(f"    Adding patient {pat} session {sesh} to database...")
                    pass

                spike_dir = Path(config.PATH_TO_DATA, "patient_data", str(pat), f"session_{sesh}", "spiking_data")
                spike_filepaths = list(spike_dir.iterdir())
                spike_filenames = sorted([s.name for s in spike_filepaths], key=helpers.extract_sort_key)

                for unit_id, filename in enumerate(spike_filenames):
                    csc_nr, unit = filename[:-4].split("_")
                    csc_index = int(csc_nr[3:]) - 1
                    print(f"    ... Unit ID: {unit_id}, CSC #: {csc_nr}, Channel index: {csc_index}")

                    channel = channel_names[csc_index]
                    print(f"    ... Channel name: {channel}")

                    unit_type, unit_nr = helpers.get_unit_type_and_number(unit)
                    print(f"    ... Unit type: {unit_type},  Within-channel unit number: {unit_nr}")

                    self.insert1({'patient_id': pat,
                                'session_nr': sesh,
                                'unit_id': unit_id, 
                                'csc': csc_nr[3:], 
                                'unit_type': unit_type, 
                                'unit_nr': unit_nr,
                                'brain_region': channel},
                                    skip_duplicates=True)
                    
                    print(" ")

@epi_schema
class MovieAnnotation(dj.Imported):
    definition = """
    # information about video annotations (e.g. labels of characters); 
    # this table contains start and end time points and values of the segments of the annotations;
    # all time points are in Neural Recording Time;
    -> Annotator                    # creator of movie annotation
    -> LabelName                    # name of annotation
    annotation_date: date           # date of annotation
    ---
    values: longblob                # list of values that represent label
    start_times: longblob           # list of start times of label segments in movie play time (PTS)
    stop_times: longblob            # list of stop times of label segments in movie play time (PTS)
    category: varchar(32)           # category of label; e.g. 'character', 'emotion', 'location'
    indicator_function: longblob    # full indicator function, one value for each movie frame
    """

    def _make_tuples(self, key):
        path_labels = Path(config.PATH_TO_LABELS)

        for filepath in path_labels.iterdir():
            label_id, label_name, annotator, date, category = filepath.name[:-4].split("_")

            try:
                check = (MovieAnnotation & f"label_name='{label_name}'" & f"category='{category}'").fetch("values")
                if len(check) > 0:
                    continue
                else: 
                    print(f"    Adding {label_name}, category {category} to database...")
                    pass
            except:
                print(f"    Adding {label_name}, category {category} to database...")
                pass

            content = np.load(filepath)

            values = np.array(content[0])
            start_times = np.array(content[1])
            stop_times = np.array(content[2])
                
            ind_func = processing_labels.make_label_from_start_stop_times(values, start_times, stop_times, config.PTS_MOVIE_new)
                
            print(f"    ... # of occurrences: {int(sum(values))}\n")

            self.insert1({'label_name': label_name,
                            'annotator_id': annotator,
                            'annotation_date': datetime.strptime(date, '%Y%m%d'),
                            'category': category,
                            'values': values,
                            'start_times': start_times,
                            'stop_times': stop_times,
                            'indicator_function': np.array(ind_func)
                            }, skip_duplicates=True)
                    

@epi_schema
class LFPData(dj.Manual):
    definition = """
    # local field potential data, by channel. 
    -> Patients
    -> Sessions
    csc_nr: int
    ---
    samples: longblob                # samples, in microvolts
    timestamps: longblob             # timestamps corresponding to each sample, in ms
    sample_rate: int                 # sample rate from the recording device
    brain_region: varchar(8)         # brain region where unit was recorded
    """

########################################################
# Table Population Functions (for dj.Manual tables) #
########################################################

def populate_lfp_data_table():
    """
    Iterates over the channel files stored in config.PATH_TO_DATA/lfp_data/
    and adds each channel to the table. 

    Ignores channels already uploaded.
    """

    patient_ids, session_nrs = MovieSession.fetch("patient_id", "session_nr")

    for i_pat, pat in enumerate(patient_ids):
        pat_sessions = session_nrs[i_pat]

        for i_sesh, sesh in enumerate(pat_sessions):
         
            path_ds_dir = Path(config.PATH_TO_PATIENT_DATA, str(pat), f"session_{sesh}", "lfp_data")
            lfp_files = list(path_ds_dir.glob("CSC*"))

            try:
                check = (LFPData & f"patient_id={pat}" & f"session_nr={sesh}").fetch("csc_nr")[0]
                if len(check) == len(lfp_files):
                    print(f"    Patient {pat} session {sesh} already added.")
                    continue
                else:
                    print(f"    Adding patient {pat} session {sesh} to database...")
                    pass
            except:
                print(f"    Adding patient {pat} session {sesh} to database...")
                pass

            path_channels = Path(config.PATH_TO_PATIENT_DATA, str(pat), f"session_{sesh}", "ChannelNames.txt")
            channel_names = helpers.get_channel_names(path_channels)

            for ds_file in path_ds_dir.iterdir():
                
                csc_nr = ds_file.name.split('_')[0][3:]
                region = channel_names[int(csc_nr)-1]
                print(f"  .. adding csc {csc_nr}..")
                ds_dict = np.load(ds_file, allow_pickle=True)
                LFPData.insert1({
                    'patient_id': pat,
                    'session_nr': sesh,
                    'csc_nr': csc_nr,
                    'samples': ds_dict.item().get("samples"),
                    'timestamps': ds_dict.item().get("timestamps"),
                    'sample_rate': ds_dict.item().get("sample_rate")[0],
                    'brain_region': region
                })


                print(f"  .. csc {csc_nr} added.")
