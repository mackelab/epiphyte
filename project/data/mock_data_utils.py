"""
Functions related to generating mock data. 
"""

import copy
import random
from random import uniform
from pathlib import Path
from collections import Counter
from datetime import datetime

import numpy as np

# local application imports 
import database.config as config
    
class GenerateData:
    """Create mock neural data (spikes, lfp) and the corresponding meta-data (channel names, anatomical location)."""
    
    def __init__(self, patient_id, session_nr):
        self.patient_id = patient_id
        self.session_nr = session_nr
        
        self.nr_channels = 80
        self.nr_units = random.randint(20, 100)
        self.nr_channels_per_region = 8
        self.unit_types = ["MU", "SU"]
        self.brain_regions = ["LA", "LAH", "LEC", "LMH", "LPHC", 
                              "RA", "RAH", "REC", "RMH", "RPCH"]

        self.rec_length = 5400000
        self.rectime_on = random.randint(1347982266000, 1695051066000)
        self.rectime_off = self.rectime_on + self.rec_length + random.randint(300000, 900000)
        
        self.datetime = datetime.utcfromtimestamp(int(self.rectime_on)/1000).strftime('%Y-%m-%d_%Hh%Mm%Ss')
        
        self.spike_trains = self.generate_spike_trains()
        self.channel_dict = self.generate_channelwise_unit_distribution()
        
    def generate_spike_trains(self):
        """
        Generates mock spike trains for a "patient."
        """
        
        spike_trains = (
            np.sort([uniform(self.rectime_on, self.rectime_off) for _ in range(int(uniform(50, 5000)))])
            for _ in range(self.nr_units)
        )
        return list(spike_trains)
    
    def generate_channelwise_unit_distribution(self):
        """
        Distributes the number of units across "channels".
        """
        
        channel_units = [
            int(random.uniform(1, self.nr_channels+1)) for _ in range(self.nr_units)
        ]
        
        channel_dict = {
            csc: [random.choice(self.unit_types) for _ in range(repeats)]
            for (csc, repeats) in Counter(channel_units).items()
        }
        
        return channel_dict
    
    def generate_channel_list(self):
        """
        Creates a list of channel names to resemble that of an actual surgical output.
        Each entry consists of "<hemisphere abbr><brain region><channel number>".
        """

        channel_list = [
            f"{region}{i+1}" 
            for region in self.brain_regions
            for i in range(self.nr_channels_per_region)
                       ]
        
        return channel_list
    
    def save_spike_trains(self, save_dir=None):
        """
        Calls the generate_spike_trains() method and resulting trains 
        in the local "data" directory, unless otherwise specified.
        """
        
        if not save_dir:
            #repo_path = config.PATH_TO_REPO TODO
            repo_path = "/home/alana/Documents/phd/code/epiphyte/project/"
            save_dir = Path(f"{repo_path}/data/patient_data/{self.patient_id}/session_{self.session_nr}/spiking_data/")
            save_dir.mkdir(parents=True, exist_ok=True)
        
        i = 0
        for csc, unit_types in self.channel_dict.items():
            su_ct = 1
            mu_ct = 1

            for t in unit_types:
                if t == "SU":
                    unit_counter = su_ct
                    su_ct += 1
                elif t == "MU":
                    unit_counter = mu_ct
                    mu_ct += 1
                
                filename = f"CSC{csc}_{t}{unit_counter}.npy"
                np.save(save_dir / filename, self.spike_trains[i])
                i += 1
                
    def save_channel_names(self, save_dir=None):
        """
        Makes and saves a txt file listing the channel names
        for each channel of the implanted "electrodes".
        """
        
        if not save_dir:
            #repo_path = config.PATH_TO_REPO TODO
            repo_path = "/home/alana/Documents/phd/code/epiphyte/project/"
            save_dir = Path(f"{repo_path}/data/patient_data/{self.patient_id}/session_{self.session_nr}/")
            save_dir.mkdir(parents=True, exist_ok=True)
            
        channel_names = self.generate_channel_list()
        
        file = save_dir / "ChannelNames.txt"
        f1 = open(file, "w+")
        for csc_name in channel_names:
            f1.write(f"{csc_name}.ncs\n")
        f1.close()

    
def generate_daq_log(patient_id, session_nr, len_context_files, signal_tile, begin_recording_time, stop_recording_time, seed=1590528227608515, stimulus_len=83.816666):
    """
    Generate mock DAQ log. 
    
    Must use same values for signal_tile and len_context_files as the events.nev mock-up
    
    params:
    stimulus_len: length of the stimulus presentation, in minutes
    
    """

    
    #uses same values for signal_tile and len_context_files as the events.nev mock-up
    values = signal_tile
    index = np.arange(len_context_files)
    
    # generate projected end time for the DAQ log, in unix time microseconds
    #movie_len_unix = (stimulus_len * 60 * 1000 * 1000)
    rec_len_unix = (stop_recording_time - begin_recording_time) 
    
    end_time = seed + rec_len_unix 
    add_interval = int((end_time - seed) / len_context_files)
    
    print("Recording length, in usec: ", rec_len_unix)
    print("End time of recording, in epoch time: ",end_time)
    print("Length of interval iteratively added: ", add_interval)
    
    pre = []
    post = []

    for i in range(len_context_files):
        interval_diff = (np.random.normal(1000, 200) / 2)

        pre.append(int(seed - interval_diff))
        post.append(int(seed + interval_diff))
        #seed += np.random.normal(1000144, 100)
        seed += add_interval 
        
    log_lines = list(zip(values, index, pre, post))


    daqsave_dir = "{}/mock_data/patient_data/{}/session_{}/daq_files/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(daqsave_dir):
        os.makedirs(daqsave_dir)

    logname_save = "{}/mock_data/patient_data/{}/session_{}/daq_files/timedDAQ-log-20200526-232347.log".format(config.PATH_TO_REPO, patient_id, session_nr)

    if os.path.exists(logname_save):
        os.remove(logname_save)

    with open(logname_save, 'a') as file:
        file.write("Initial signature: 255	255\n255\t255\t\ndata\tStamp\tpre\tpost\n")
        for datum in log_lines:
            file.write("{}\t{}\t{}\t{}\n".format(datum[0], datum[1], datum[2], datum[3]))
        file.close()
    

    
def generate_perfect_watchlog(patient_id, session_nr, seed=1590528227608515):
    """
    Generate a movie watchlog file without pauses or skips.
    """

    nr_movie_frames = 125725      # movie length: 5029 seconds (AVI file); 5029/0.04 = 125725
    perfect_pts = [round((x * 0.04), 2) for x in range(1, nr_movie_frames+1)]  
    
    cpu_time = []

    for i in range(nr_movie_frames):
        seed += 41000
        cpu_time.append(seed)

    wlsave_dir = "{}/mock_data/patient_data/{}/session_{}/watchlogs/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(wlsave_dir):
        os.makedirs(wlsave_dir)

    wl_name_save = "{}/mock_data/patient_data/{}/session_{}/watchlogs/ffplay-watchlog-20200526-232347.log".format(config.PATH_TO_REPO, patient_id, session_nr)

    if os.path.exists(wl_name_save):
        os.remove(wl_name_save)

    with open(wl_name_save, 'a') as file:
        file.write("movie_stimulus.avi\n")
        for i in range(nr_movie_frames):
            file.write("pts\t{}\ttime\t{}\n".format(perfect_pts[i], cpu_time[i]))
        file.close()
        
        
def generate_playback_artifacts(patient_id, session_nr, seed=1590528227608515, stimulus_len=83.816666): 
    """
    Generate a movie watchlog file with pauses and skips.
    """
    nr_movie_frames = 125725      # movie length: 5029 seconds (AVI file); 5029/0.04 = 125725
    perfect_pts = [round((x * 0.04), 2) for x in range(1, nr_movie_frames+1)]  
    
    pause_pool = 5 * 1000 * 1000 * 60 # 5 minutes in unix/epoch time -- use for max pause time
    
    wl_seed = seed + 1e9
    # generate projected end time for the DAQ log, in unix time microseconds
    movie_len_unix = (stimulus_len * 60 * 1000 * 1000) - pause_pool
    end_time = seed + movie_len_unix 
    add_interval = int((end_time - seed) / nr_movie_frames)
    
    print("Length of the stimulus, in usec: ", movie_len_unix)
    print("End of stimulus, in epoch time: ", end_time)
    print("Length of interval iteratively added : ", add_interval)
    
    cpu_time = []
    
    for i in range(nr_movie_frames):
        wl_seed += add_interval
        cpu_time.append(int(wl_seed))   
    
    ####
    
    ## add in pauses
    nr_pauses = int(uniform(1,6))
    min_pause = 0.1 * 1000 * 1000 * 60
    
    # randomly select indices from perfect watchlog 
    indices_pause = random.sample(range(len(cpu_time) - 5000), nr_pauses)
        
    cpu_time = np.array(cpu_time)
    
    for i, index in enumerate(indices_pause): 
        if (len(indices_pause) - i) > 0: 
            pause_len = random.randint(min_pause, pause_pool)
            #pause_len = int(random.sample(range(min_pause, pause_pool))) ## TODO: this might be causing too big a difference btw wl and daq
            cpu_time = np.concatenate((cpu_time[:index],cpu_time[index:] + pause_len)) 
            pause_pool -= pause_len
        else:
            pause_len = pause_pool
            cpu_time = np.concatenate((cpu_time[:index],cpu_time[index:] + pause_len))

    # randomly select indices from perfect watchlog 
    nr_skips = int(uniform(1,4))
    
    indices_skip = random.sample(range(len(perfect_pts) - 5000), nr_skips)

    skip_pts = np.array(copy.copy(perfect_pts))
    
    max_skip = 500

    for i, index in enumerate(indices_skip): 
        # note: careful about values here -- can exceed mocked movie length. 
        # currently set so that the max possible skip is the penultimate frame
        if len(indices_skip) > 1:
            skip_len = int(uniform((max_skip * -1), max_skip))
            skip_pts = np.concatenate((skip_pts[:index],skip_pts[index:] + skip_len)) 
            max_skip -= skip_len

        if len(indices_skip) == 1:
            skip_len = max_skip
            skip_pts = np.concatenate((skip_pts[:index],skip_pts[index:] + skip_len)) 

    # test for rounding issue
    skip_pts = [round(frame, 2) for frame in skip_pts]

    # prevents generated frame from exceeding the mock movie length
    skip_pts_revised = []
    for i, frame in enumerate(skip_pts):
        if frame > (nr_movie_frames * 0.04):
            skip_pts_revised.append(nr_movie_frames * 0.04)
        if frame <= (nr_movie_frames * 0.04):
            skip_pts_revised.append(frame)
        if frame < 0: 
            skip_pts_revised.append(0.0)
    
    ####

    wlsave_dir = "{}/mock_data/patient_data/{}/session_{}/watchlogs/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(wlsave_dir):
        os.makedirs(wlsave_dir)

    wl_name_save = "{}/mock_data/patient_data/{}/session_{}/watchlogs/ffplay-watchlog-20200526-232347.log".format(config.PATH_TO_REPO, patient_id, session_nr)

    if os.path.exists(wl_name_save):
        os.remove(wl_name_save)
        
    with open(wl_name_save, 'a') as file:
        file.write("movie_stimulus.avi\n")
        for i in range(nr_movie_frames):
            if i not in indices_pause:
                file.write("pts\t{}\ttime\t{}\n".format(skip_pts_revised[i], cpu_time[i]))
            if i in indices_pause: 
                file.write("Pausing\nContinuing\tafter\tpause\n")
    
    file.close()

    
def make_events_and_daq(patient_id, session_nr, begin_recording_time, stop_recording_time, seed=1590528227608515, stimulus_len=83.816666):
    """
    Put together events and daq code, compute all at once. 
    """
    len_context_files, signal_tile = generate_pings()
    
    generate_events(patient_id, session_nr, len_context_files, signal_tile, begin_recording_time, stop_recording_time)
    generate_daq_log(patient_id, session_nr, len_context_files, signal_tile, begin_recording_time, stop_recording_time, seed, stimulus_len)
    