"""
Functions related to generating mock data. 
"""

import os
import sys
import numpy as np
import random
from random import uniform

# local application imports 
import database.config as config
    
    
def generate_spikes(patient_id, session_nr, nr_units, begin_recording_time, stop_recording_time):
    """
    Generates mock spike trains for a "patient."
    
    Writes spike trains to file as numpy binaries. 
    
    """
    spikes = []
    for i in range(nr_units):
        nr_spikes = int(uniform(10000, 16000))
        spike_vec = []
        for j in range(nr_spikes):
            spike_vec.append(uniform(begin_recording_time, stop_recording_time))
        spikes.append(spike_vec)
    
    # Directory set-up
    save_dir = "{}/mock_data/patient_data/{}/session_{}/spiking_data/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    unit_types = ['M', 'S']
    for i in range((nr_units)):
        ## NOTE: because of the random naming scheme, re-running this
        ## code will cause issues later in the pipeline (too many file for 
        ## number of expected units)
        np.save(os.path.join(save_dir, "CSC{}_{}UA{}.npy".format(i+1, random.choice(unit_types), '1')), spikes[i])    
    

def generate_channel_file(patient_id, session_nr, nr_unit, nr_units_per_brain_region=None):
    """
    Generates ChannelNames.txt file. 
    
    If not given an array-like containing the number of units to 
    assign to each brain region, will automatically generate. 
    """
    brain_regions = ["LA", "LAH", 'LEC', "LMH", "LPHC", "RA", "RAH", "REC", "RMH", "RPCH"]

    # Generate number of units per brain region
    if not nr_units_per_brain_region:
        nr_units_per_brain_region = []
        
        seed = nr_unit / 10
        counter = nr_unit
        for i in range(len(brain_regions)):
            if i != len(brain_regions):
                random_int = int(np.random.normal(loc=seed, scale=2.0))
                nr_units_per_brain_region.append(random_int)
                counter -= random_int 
            if i == len(brain_regions):
                nr_units_per_brain_region.append(counter)
                
    assert sum(nr_units_per_brain_region) == nr_unit, "Number of units per brain region doesn't match total units."
    
    channel_save_file = "{}/mock_data/session_data/session_{}_{}_20190101_12h00m00s/ChannelNames.txt".format(config.PATH_TO_REPO, patient_id, session_nr)

    if os.path.exists(channel_save_file):
        os.remove(channel_save_file)
        
    channel_save_dir = "{}/mock_data/session_data/session_{}_{}_20190101_12h00m00s/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(channel_save_dir):
        os.makedirs(channel_save_dir)
    
    f1 = open("{}/mock_data/session_data/session_{}_{}_20190101_12h00m00s/ChannelNames.txt".format(config.PATH_TO_REPO, patient_id, session_nr), 'w+')
    for i in range(len(nr_units_per_brain_region)):
        for j in range(nr_units_per_brain_region[i]):
            f1.write("{}{}.ncs\n".format(brain_regions[i], j+1))

    f1.close()
    
    
def generate_pings():
    """
    Recreate how Neurolynx interfaces with a local computer. 
    """
    len_context_files = random.randint(100, 200) # generate length of events.nev & DAQ file. 

    # recreate pings
    if len_context_files % 8 == 0:
        reps = int(len_context_files / 8)
    else:
        reps = int(len_context_files / 8) + 1

    signal_tile = np.tile([1,2,4,8,16,32,64,128], reps)
    signal_tile = signal_tile[:len_context_files]
    
    return len_context_files, signal_tile
    
def generate_events(patient_id, session_nr, len_context_files, signal_tile, begin_recording_time, stop_recording_time):
    """
    Generate mock Events.nev file. Save as Events.npy file. 
    """
    
    # recreate event timestamps
    events = np.linspace(begin_recording_time, stop_recording_time, num=len_context_files)

    events_mat = np.array(list(zip(events, signal_tile)))

    evsave_dir = "{}/mock_data/patient_data/{}/session_{}/event_file/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(evsave_dir):
        os.makedirs(evsave_dir)

    evname_save = "{}/mock_data/patient_data/{}/session_{}/event_file/Events.npy".format(config.PATH_TO_REPO, patient_id, session_nr)

    if os.path.exists(evname_save):
        os.remove(evname_save)

    np.save(evname_save, events_mat)
    
def generate_daq_log(patient_id, session_nr, len_context_files, signal_tile, seed=1590528227608515):
    """
    Generate mock DAQ log. 
    
    Must use same values for signal_tile and len_context_files as the events.nev mock-up
    """
    #uses same values for signal_tile and len_context_files as the events.nev mock-up
    values = signal_tile
    index = np.arange(len_context_files)

    pre = []
    post = []

    for i in range(len_context_files):
        interval_diff = (np.random.normal(2575, 305) / 2)

        pre.append(int(seed - interval_diff))
        post.append(int(seed + interval_diff))
        seed += np.random.normal(1000144, 100)

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
    
def make_events_and_daq(patient_id, session_nr, begin_recording_time, stop_recording_time, seed=1590528227608515):
    """
    Put together events and daq code, compute all at once. 
    """
    len_context_files, signal_tile = generate_pings()
    
    generate_events(patient_id, session_nr, len_context_files, signal_tile, begin_recording_time, stop_recording_time)
    generate_daq_log(patient_id, session_nr, len_context_files, signal_tile, seed)
    
    
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
        
def generate_playback_artifacts(patient_id, session_nr, seed=1590528227608515):
    """
    Generate a movie watchlog file with pauses and skips.
    """
    
    nr_movie_frames = 125725      # movie length: 5029 seconds (AVI file); 5029/0.04 = 125725
    perfect_pts = [round((x * 0.04), 2) for x in range(1, nr_movie_frames+1)]  

    cpu_time = []

    for i in range(nr_movie_frames):
        seed += 41000
        cpu_time.append(seed)    
        
    ## add in pauses
    nr_pauses = int(uniform(1,6))

    # randomly select indices from perfect watchlog 
    indices = random.sample(range(len(cpu_time)), nr_pauses)
    
    for i, index in enumerate(indices): 
        pause_len = int(uniform(100000000, 3000000000))
        cpu_time = np.concatenate((cpu_time[:index],cpu_time[index:] + pause_len)) 
        
    nr_skips = int(uniform(1,4))

    # randomly select indices from perfect watchlog 
    indices = random.sample(range(len(perfect_pts)), nr_skips)

    skip_pts = np.array(copy.copy(perfect_pts))
    
    for i, index in enumerate(indices): 
        skip_len = int(uniform(10, 2000))
        skip_pts = np.concatenate((skip_pts[:index],skip_pts[index:] + skip_len)) 
    
    
    wlsave_dir = "{}/mock_data/patient_data/{}/session_{}/watchlogs/".format(config.PATH_TO_REPO, patient_id, session_nr)

    if not os.path.exists(wlsave_dir):
        os.makedirs(wlsave_dir)

    wl_name_save = "{}/mock_data/patient_data/{}/session_{}/watchlogs/ffplay-watchlog-20200526-232347.log".format(config.PATH_TO_REPO, patient_id, session_nr)

    if os.path.exists(wl_name_save):
        os.remove(wl_name_save)
        
    with open(wl_name_save, 'a') as file:
    file.write("movie_stimulus.avi\n")
    for i in range(nr_movie_frames):
        if i not in indices:
            file.write("pts\t{}\ttime\t{}\n".format(skip_pts[i], cpu_time[i]))
        if i in indices: 
            file.write("Pausing\nContinuing\tafter\tpause")
    file.close()