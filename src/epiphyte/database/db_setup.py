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
