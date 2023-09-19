"""
Class object which generates and saves mock data.
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
    """
    Create mock neural data (spikes, lfp) 
    and the corresponding meta-data (channel names, anatomical location).
    Also creates the 
    """
    
    def __init__(self, patient_id, session_nr, stimulus_len=83.33):
        
        self.patient_id = patient_id
        self.session_nr = session_nr
        self.stimulus_len = stimulus_len
        
        self.nr_channels = 80
        self.nr_units = random.randint(20, 100)
        self.nr_channels_per_region = 8
        self.unit_types = ["MU", "SU"]
        self.brain_regions = ["LA", "LAH", "LEC", "LMH", "LPHC", 
                              "RA", "RAH", "REC", "RMH", "RPCH"]

        self.rec_length = 5400000
        self.rectime_on = random.randint(1347982266000, 1695051066000)
        self.rectime_off = self.rectime_on + self.rec_length + random.randint(300000, 900000)
        
        self.spike_trains = self.generate_spike_trains()
        self.channel_dict = self.generate_channelwise_unit_distribution()
        
        ## stimulus data
        
        self.len_context_files = random.randint(4000, 5400) # generate length of events.nev & DAQ file. 
        self.datetime = datetime.utcfromtimestamp(int(self.rectime_on)/1000).strftime('%Y-%m-%d_%Hh%Mm%Ss')
        
        self.signal_tile = self.generate_pings()
        self.stim_on_time = self.generate_stimulus_onsets()[0]
        self.stim_off_time = self.generate_stimulus_onsets()[1]
    
    def summarize(self):
        """
        Prints out a selection of randomized variables.
        """
        
        print(f"# of 'neurons': {self.nr_units}")
        print(f"Date of recording session: {self.datetime}")

        
    def format_save_dir(self, subdir=None):
        """
        Formats the subdir in which everything will be saved.
        """

        save_dir = Path(f"/home/alana/Documents/phd/code/epiphyte/project/data/patient_data/{self.patient_id}/session_{self.session_nr}/")
            
        if subdir:
            save_dir = save_dir / subdir
            
        save_dir.mkdir(parents=True, exist_ok=True)
               
        return save_dir
            
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

        save_dir = self.format_save_dir(subdir="spiking_data")
        
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
                   
        save_dir = self.format_save_dir()
            
        channel_names = self.generate_channel_list()
        
        file = save_dir / "ChannelNames.txt"
        f1 = open(file, "w+")
        for csc_name in channel_names:
            f1.write(f"{csc_name}.ncs\n")
        f1.close()
    
    ##############
    ## stimulus data generation
    ##############
    
    def generate_pings(self):
        """
        Recreate how Neuralynx interfaces with a local computer. 
        """       
        # recreate pings
        if self.len_context_files % 8 == 0:
            reps = int(self.len_context_files / 8)
        else:
            reps = int(self.len_context_files / 8) + 1

        signal_tile = np.tile([1,2,4,8,16,32,64,128], reps)
        signal_tile = signal_tile[:self.len_context_files]

        return signal_tile
    
    def generate_events(self):
        """
        Generate mock Events.nev file. Save as Events.npy file. 
        """

        # recreate event timestamps
        events = np.linspace(self.rectime_on, self.rectime_off, num=self.len_context_files)
        events_mat = np.array(list(zip(events, self.signal_tile)))
        
        return events, events_mat
    
    def save_events(self, save_dir=None):
        """
        Save the generated mock Events.npy file. 
        """
        
        events, events_mat = self.generate_events()
        
        save_dir = self.format_save_dir(subdir="event_file")
        
        ev_name = save_dir / "Events.npy"
        
        np.save(ev_name, events_mat)
        
    def generate_stimulus_onsets(self):
        """
        Generate the onset and offset timestamps for the stimulus.
        """
        
        # generate projected end time for the DAQ log, in unix time microseconds
        # movie_len_unix = (stimulus_len * 60 * 1000 * 1000)       
        stim_on_time = (self.rectime_on + random.randint(120000, 180000)) * 1000
        stim_off_time = (stim_on_time + (self.stimulus_len * 60 * 1000)) * 1000
        
        return stim_on_time, stim_off_time
    
    def seed_and_interval(self):
        
        add_interval = int((self.stim_off_time) / self.len_context_files)
        seed = int(self.stim_on_time + add_interval*1.25)
        return add_interval, seed
        
    def generate_daq_log(self):
        """
        Generate the DAQ log. 
        """
        
        add_interval, seed = self.seed_and_interval()
        
        pre = []
        post = []

        for i in range(self.len_context_files):
            interval_diff = (np.random.normal(1000, 200) / 2)

            pre.append(int(seed - interval_diff))
            post.append(int(seed + interval_diff))
            seed += add_interval 

        return list(zip(self.signal_tile, np.arange(self.len_context_files), pre, post))
    
    def save_daq_log(self):
        """
        Saves the generated DAQ log.
        """
        
        log_lines = self.generate_daq_log()
        
        save_dir = self.format_save_dir(subdir="daq_files")
        log_loc = save_dir / f"timedDAQ-log-{self.datetime}.log"
        
        with open(log_loc, 'a') as file:
            file.write("Initial signature: 255	255\n255\t255\t\ndata\tStamp\tpre\tpost\n")
            for datum in log_lines:
                file.write("{}\t{}\t{}\t{}\n".format(datum[0], datum[1], datum[2], datum[3]))
            file.close()
            
    def generate_perfect_watchlog(self):
        """
        Generate a movie watchlog file without pauses or skips.
        """
        
        _, seed = self.seed_and_interval()
        
        nr_movie_frames = int(self.stimulus_len * 60 / 0.04)
        perfect_pts = [round((x * 0.04), 2) for x in range(1, nr_movie_frames+1)] 
        
        cpu_time = []
        for i in range(nr_movie_frames):
            seed += 41000
            cpu_time.append(seed)
        
        return nr_movie_frames, perfect_pts, cpu_time
    
    def save_perfect_watchlog(self):
        
        nr_movie_frames, perfect_pts, cpu_time = self.generate_perfect_watchlog()
        
        save_dir = self.format_save_dir(subdir="watchlogs")
        
        wl_name = f"ffplay-watchlog-{self.datetime}.log"
        
        with open(save_dir / wl_name, 'a') as file:
            file.write("movie_stimulus.avi\n")
            for i in range(nr_movie_frames):
                file.write("pts\t{}\ttime\t{}\n".format(perfect_pts[i], cpu_time[i]))
            file.close()
    
    def make_pauses_and_skips(self):
        """
        Generate a movie watchlog file with pauses and skips.
        """
        nr_movie_frames, perfect_pts, cpu_time = self.generate_perfect_watchlog()
        _, seed = self.seed_and_interval()
        pause_pool = 5 * 1000 * 1000 * 60 # 5 minutes in unix/epoch time -- use for max pause time        movie_len_unix = (self.stimulus_len * 60 * 1000 * 1000) - pause_pool
        
        movie_len_unix = (self.stimulus_len * 60 * 1000 * 1000) - pause_pool
        end_time = seed + movie_len_unix 
        add_interval = int((end_time - seed) / nr_movie_frames)
        
        cpu_time = []
        for i in range(nr_movie_frames):
            seed += add_interval
            cpu_time.append(int(seed))   

        nr_pauses = int(uniform(1,6))
        min_pause = 0.1 * 1000 * 1000 * 60
        
        indices_pause = random.sample(range(len(cpu_time) - 5000), nr_pauses)
        
        cpu_time = np.array(cpu_time)
        
        for i, index in enumerate(indices_pause): 
            if (len(indices_pause) - i) > 0: 
                pause_len = random.randint(min_pause, pause_pool)
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

        
        return nr_movie_frames, skip_pts_revised, cpu_time, indices_pause
        
    def save_watchlog_with_artifacts(self):
        """
        Save watchlog with artifacts.
        """
        nr_movie_frames, skip_pts_revised, cpu_time, indices_pause = self.make_pauses_and_skips()
    
        # save
        save_dir = self.format_save_dir(subdir="watchlogs")
        wl_name = f"ffplay-watchlog-{self.datetime}.log"
        
        with open(save_dir / wl_name, 'a') as file:
            file.write("movie_stimulus.avi\n")
            for i in range(nr_movie_frames):
                if i not in indices_pause:
                    file.write("pts\t{}\ttime\t{}\n".format(skip_pts_revised[i], cpu_time[i]))
                if i in indices_pause: 
                    file.write("Pausing\nContinuing\tafter\tpause\n")

        file.close()