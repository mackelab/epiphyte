"""Mock neural-data generator and file writer.

This module contains GenerateData, which synthesizes spike trains,
LFP-like signals, channel metadata, event streams, DAQ logs, and watchlogs, and
for saves them to the on-disk layout expected by Epiphyte. Constants such as
output roots (e.g., PATH_TO_DATA, PATH_TO_LABELS), annotation metadata
(e.g., annotators), and spike-shape parameters are read from
epiphyte.database.config and .mock_data_inits.

Example:
    ```python
    from epiphyte.data.mock_data_utils import GenerateData

    gen = GenerateData(patient_id=1, session_nr=1, stimulus_len=83.33)
    gen.summarize()
    gen.save_session_info()
    gen.save_spike_trains()
    gen.save_lfp_data()
    gen.save_channel_names()
    gen.save_events()
    gen.save_daq_log()
    gen.save_watchlog_with_artifacts()
    ```

Running the module as a script executes run_data_generation(), which creates a
small demo dataset for a few patients/sessions.

Outputs & directory layout:

    Created under:
        {PATH_TO_DATA}/patient_data/{patient_id}/session_{session_nr}/

    - session_info.npy
        Dict with keys: patient_id, session_nr, date, time
    - ChannelNames.txt
        One ".ncs" channel name per line
    - spiking_data/CSC{channel}_{MU|SU}{idx}.npy
        Dict with "spike_times" (ms, Unix epoch) and "spike_amps" (waveform arrays)
    - lfp_data/CSC1_lfp.npy
        Dict with "ts" (ms, Unix epoch) and "samples" (1 kHz sine)
    - event_file/Events.npy
        Rows of (timestamp, code); codes tile over [1, 2, 4, 8, 16, 32, 64, 128]
    - daq_files/timedDAQ-log-<YYYY-mm-dd_HH-MM-SS>.log
        Tabular DAQ log
    - watchlogs/ffplay-watchlog-<YYYY-mm-dd_HH-MM-SS>.log
        PTS/CPU-time log with pauses/skips

    Annotation stubs are written to:
        {PATH_TO_LABELS}/
    as simple *.npy arrays with on/off segments.

Conventions:
    - Time bases:
        * Spike times / LFP timestamps: milliseconds since Unix epoch
        * stim_on_time / stim_off_time: microseconds since Unix epoch
        * Watchlog PTS increments: ~0.04 s per frame
    - Sampling: LFP synthesized at 1 kHz
    - Randomness: Data are randomized per run (no fixed seed by default)

Public API:
    - GenerateData: main generator with save_* methods for each artifact
    - run_data_generation(): convenience entry point to populate a demo dataset

Notes:
    - Relies on configuration constants from epiphyte.database.config and
      waveform shape parameters from .mock_data_inits.
    - Use GenerateData.summarize() to quickly inspect randomized session settings.
    - For reproducible outputs, set seeds in both random and numpy.random
      before instantiation.
"""
from __future__ import annotations

import copy
import random
from random import uniform
from pathlib import Path
from collections import Counter
from datetime import datetime

import numpy as np

from typing import List, Tuple

from epiphyte.database.config import *  # noqa: F401,F403 (imports constants)
from .mock_data_inits import *  # noqa: F401,F403 (imports spike shape params)

class GenerateData:
    """Generate mock neural data and related metadata.

    Attributes:
        patient_id (int): Integer identifier for the mock patient.
        session_nr (int): Session number for this recording.
        stimulus_len (float): Stimulus length in minutes.
        nr_channels (int): Number of channels simulated.
        nr_units (int): Number of units across all channels.
        nr_channels_per_region (int): Channels per brain region label.
        unit_types (enum): Allowed unit type codes (e.g., ``"MU"``, ``"SU"``).
        brain_regions (List[str]): Region codes used to synthesize channel names.
        rec_length (int): Recording length in milliseconds.
        rectime_on (int): Start time (unix epoch ms) for recording.
        rectime_off (int): End time (unix epoch ms) for recording.
        spike_times (List[np.ndarray]): Generated spike time arrays per unit.
        spike_amps (List[np.ndarray]): Generated spike amplitude arrays per unit.
        channel_dict (dict): Mapping of channel index to list of unit types.
        sampling_rate (int): LFP sampling rate (Hz) used in mock signal.
        len_context_files (int): Number of entries for events/DAQ logs.
        datetime (str): ISO-like timestamp used in filenames.
        signal_tile (np.ndarray): Bit-pattern tile used to synthesize event codes.
        stim_on_time (int): Estimated stimulus onset (microseconds).
        stim_off_time (int): Estimated stimulus offset (microseconds).
    """
    
    def __init__(self, patient_id: int, session_nr: int,
                 stimulus_len: float = 83.33) -> None:
        
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
        
        self.spike_times, self.spike_amps = self.generate_spike_trains()
        self.channel_dict = self.generate_channelwise_unit_distribution()
        
        self.sampling_rate = 1000
        ## stimulus data
        
        self.len_context_files = random.randint(4000, 5400) # generate length of events.nev & DAQ file. 
        self.datetime = datetime.utcfromtimestamp(int(self.rectime_on)/1000).strftime('%Y-%m-%d_%H-%M-%S')
        
        self.signal_tile = self.generate_pings()
        self.stim_on_time = self.generate_stimulus_onsets()[0]
        self.stim_off_time = self.generate_stimulus_onsets()[1]
    
    def summarize(self) -> None:
        """Print key randomized parameters for quick inspection."""
        
        print(f"# of 'neurons': {self.nr_units}")
        print(f"Date of recording session: {self.datetime}")

        
    def format_save_dir(self, subdir: str | None = None) -> Path:
        """Build and ensure the output directory exists.

        Args:
            subdir: Optional subdirectory under the session path.

        Returns:
            Path: Absolute path to the created directory:
                ``{PATH_TO_DATA}/patient_data/{patient_id}/session_{session_nr}/[subdir]``.
        """

        save_dir = Path(f"{PATH_TO_DATA}/patient_data/{self.patient_id}/session_{self.session_nr}/")
            
        if subdir:
            save_dir = save_dir / subdir
            
        save_dir.mkdir(parents=True, exist_ok=True)
               
        return save_dir
            
    def generate_spike_trains(self) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Generate mock spike trains and amplitudes for all units.

        Returns:
            Tuple[List[np.ndarray], List[np.ndarray]]: ``(spike_times, spike_amps)``

            - ``spike_times``: list of length ``nr_units``; each element is a
              sorted ``float`` array of spike times in Unix epoch **ms**.
            - ``spike_amps``: list of length ``nr_units``; each element is a
              ``(n_spikes, 64)`` array of waveform-like amplitudes.

        Notes:
            The number of spikes per unit is randomized per unit.
        """
        
        spike_times = [
            np.sort([uniform(self.rectime_on, self.rectime_off) for _ in range(int(uniform(50, 5000)))])
            for _ in range(self.nr_units)
        ]

        spike_amps = []
        for s_t in spike_times:
        
            new_amps = np.random.normal(loc=spike_shape_u, scale=spike_shape_sd, size=(len(s_t), 64))
            spike_amps.append(new_amps)

        return spike_times, spike_amps
    
    def generate_channelwise_unit_distribution(self) -> dict[int, List[str]]:
        """Distribute units across channels and assign unit types.

        Returns:
            dict[int, List[str]]: Mapping from channel index (1-based) to a list
            of unit-type codes (e.g., ``["MU", "SU", ...]``).
        """
        
        channel_units = [
            int(random.uniform(1, self.nr_channels+1)) for _ in range(self.nr_units)
        ]
        
        channel_dict = {
            csc: [random.choice(self.unit_types) for _ in range(repeats)]
            for (csc, repeats) in Counter(channel_units).items()
        }
        
        return channel_dict
    
    def generate_lfp_channel(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate a simple sine-wave LFP-like channel.

        Returns:
            Tuple[np.ndarray, np.ndarray]: ``(timestamps_ms, samples)`` where
            ``timestamps_ms`` are Unix epoch **ms** and ``samples`` is a float
            array representing an 8 Hz sine wave at 1 kHz.
        """
        ts = np.arange(self.rectime_on, self.rectime_off,1)
        frequency = 8  # in Hz
        amplitude = 100  # arbitrary unit
        samples = amplitude * np.sin(2 * np.pi * frequency * ts)
        return ts, samples

    def generate_channel_list(self) -> List[str]:
        """Create channel names like ``LA1``, ``LA2``, ..., ``RPCH8``.

        Returns:
            List[str]: List of channel name strings.
        """

        channel_list = [
            f"{region}{i+1}" 
            for region in self.brain_regions
            for i in range(self.nr_channels_per_region)
                       ]
        
        return channel_list
    
    def save_spike_trains(self) -> None:
        """Save generated spike trains and amplitudes as ``.npy`` files.

        Writes:
            ``spiking_data/CSC{channel}_{TYPE}{idx}.npy`` under the session
            directory. Each file contains a dict with keys:

            - ``"spike_times"``: Unix epoch **ms** (1D array)
            - ``"spike_amps"``: waveform amplitudes, shape ``(n_spikes, 64)``
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
                
                save_dict = {
                    "spike_times": self.spike_times[i], 
                    "spike_amps": self.spike_amps[i]
                }

                filename = f"CSC{csc}_{t}{unit_counter}.npy"
                np.save(save_dir / filename, save_dict)
                i += 1

    def save_lfp_data(self) -> None:
        """Generate and save the LFP channel as ``CSC1_lfp.npy``.

        Writes:
            ``lfp_data/CSC1_lfp.npy`` containing a dict with:

            - ``"ts"``: timestamps (Unix epoch **ms**)
            - ``"samples"``: LFP-like samples at 1 kHz

        Notes: 
            Only one LFP channel is generated due to the size of each channel. 
            A single channel suffices for demonstration purposes.
            If you include field potential data, consider using a large-storage backend.
        """
        save_dir = self.format_save_dir(subdir="lfp_data")

        ts, samples = self.generate_lfp_channel()

        filename = f"CSC1_lfp.npy"
        np.save(save_dir / filename, {"ts": ts, "samples": samples})
    
    def save_channel_names(self) -> None:
        """Save ``ChannelNames.txt`` listing channel names one per line.

        Writes:
            ``ChannelNames.txt`` in the session root. Each line ends with
            ``.ncs`` (e.g., ``LA1.ncs``).
        """        
        save_dir = self.format_save_dir()
            
        channel_names = self.generate_channel_list()
        
        file = save_dir / "ChannelNames.txt"
        f1 = open(file, "w+")
        for csc_name in channel_names:
            f1.write(f"{csc_name}.ncs\n")
        f1.close()

    def save_session_info(self) -> None:
        """Save a ``session_info.npy`` dictionary.

        Writes:
            ``session_info.npy`` containing a dict with
            ``patient_id``, ``session_nr``, ``date``, and ``time`` (UTC).
        """
        save_dir = self.format_save_dir()

        date, time = self.datetime.split("_")
        session_info = {
            "patient_id": self.patient_id,
            "session_nr": self.session_nr,
            "date": date, 
            "time": time
        }
        np.save(save_dir / "session_info.npy", session_info)
        
    ## stimulus data generation
    
    def generate_pings(self) -> np.ndarray:
        """Create a repeating event-code tile.

        Returns:
            np.ndarray: 1D integer array of length ``len_context_files`` with
            elements tiled from ``[1, 2, 4, 8, 16, 32, 64, 128]``.
        """
        # recreate pings
        if self.len_context_files % 8 == 0:
            reps = int(self.len_context_files / 8)
        else:
            reps = int(self.len_context_files / 8) + 1

        signal_tile = np.tile([1,2,4,8,16,32,64,128], reps)
        signal_tile = signal_tile[:self.len_context_files]

        return signal_tile
    
    def generate_events(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate mock event timestamps and (timestamp, code) matrix.

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - ``events``: 1D float array of Unix epoch **ms** timestamps.
                - ``events_mat``: 2D array with rows ``(timestamp_ms, code)``.
        """

        # recreate event timestamps
        events = np.linspace(self.rectime_on, self.rectime_off, num=self.len_context_files)
        events_mat = np.array(list(zip(events, self.signal_tile)))
        
        return events, events_mat
    
    def save_events(self) -> None:
        """Save generated events to ``event_file/Events.npy``."""
        
        events, events_mat = self.generate_events()
        
        save_dir = self.format_save_dir(subdir="event_file")
        
        ev_name = save_dir / "Events.npy"
        
        np.save(ev_name, events_mat)
        
    def generate_stimulus_onsets(self) -> Tuple[int, int]:
        """Generate approximate onset and offset timestamps for the stimulus.

        Returns:
            Tuple[int, int]: ``(stim_on_time, stim_off_time)`` in Unix epoch **µs**.
        """
        
        # generate projected end time for the DAQ log, in unix time microseconds
        # movie_len_unix = (stimulus_len * 60 * 1000 * 1000)       
        stim_on_time = (self.rectime_on + random.randint(120000, 180000)) * 1000
        stim_off_time = (stim_on_time + (self.stimulus_len * 60 * 1000)) * 1000
        
        return stim_on_time, stim_off_time
    
    def seed_and_interval(self) -> Tuple[int, int]:
        """Compute DAQ interval and initial seed time for log synthesis.

        Returns:
            Tuple[int, int]: ``(interval_us, seed_time_us)`` in **microseconds**.
        """

        add_interval = int((self.stim_off_time) / self.len_context_files)
        seed = int(self.stim_on_time + add_interval * 1.25)
        return add_interval, seed
        
    def generate_daq_log(self) -> List[Tuple[int, int, int, int]]:
        """Generate DAQ log entries.

        Each entry is a tuple ``(code, idx, pre_us, post_us)``.

        Returns:
            List[Tuple[int, int, int, int]]: DAQ log with one row per event.
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
    
    def save_daq_log(self) -> None:
        """Save the generated DAQ log as a text file in ``daq_files``."""
        
        log_lines = self.generate_daq_log()
        
        save_dir = self.format_save_dir(subdir="daq_files")
        log_loc = save_dir / f"timedDAQ-log-{self.datetime}.log"
        
        with open(log_loc, 'a') as file:
            file.write("Initial signature: 255	255\n255\t255\t\ndata\tStamp\tpre\tpost\n")
            for datum in log_lines:
                file.write("{}\t{}\t{}\t{}\n".format(datum[0], datum[1], datum[2], datum[3]))
            file.close()
            
    def generate_perfect_watchlog(self) -> Tuple[int, List[float], List[int]]:
        """Generate watchlog without pauses or skips.

        Returns:
            Tuple[int, List[float], List[int]]:
                - ``nr_movie_frames``: Number of frames (≈ stimulus_len / 0.04s).
                - ``perfect_pts``: PTS values (seconds), 0.04 s increments.
                - ``cpu_time``: Corresponding Unix epoch **µs** timestamps.
        """
        
        _, seed = self.seed_and_interval()
        
        nr_movie_frames = int(self.stimulus_len * 60 / 0.04)
        perfect_pts = [round((x * 0.04), 2) for x in range(1, nr_movie_frames+1)] 
        
        cpu_time = []
        for i in range(nr_movie_frames):
            seed += 41000
            cpu_time.append(seed)
        
        return nr_movie_frames, perfect_pts, cpu_time
    
    def save_perfect_watchlog(self) -> None:
        """Write a perfect (no pauses/skips) watchlog to ``watchlogs``."""
        nr_movie_frames, perfect_pts, cpu_time = self.generate_perfect_watchlog()
        
        save_dir = self.format_save_dir(subdir="watchlogs")
        
        wl_name = f"ffplay-watchlog-{self.datetime}.log"
        
        with open(save_dir / wl_name, 'a') as file:
            file.write("movie_stimulus.avi\n")
            for i in range(nr_movie_frames):
                file.write("pts\t{}\ttime\t{}\n".format(perfect_pts[i], cpu_time[i]))
            file.close()
    
    def make_pauses_and_skips(self) -> Tuple[int, List[float], List[int], List[int]]:
        """Generate a watchlog with pauses and skips.

        Returns:
            Tuple[int, List[float], List[int], List[int]]:
                - ``nr_movie_frames``: Number of frames.
                - ``pts``: PTS values (seconds) after inserting skips.
                - ``cpu_time``: Unix epoch **µs** timestamps per frame.
                - ``indices_pause``: Frame indices at which a pause occurred.

        Notes:
            Pause lengths and skip magnitudes are randomized. PTS values are
            clamped to the movie duration and non-negative.
        """
        nr_movie_frames, perfect_pts, cpu_time = self.generate_perfect_watchlog()
        _, seed = self.seed_and_interval()
        pause_pool = 1 * 1000 * 1000 * 60 # 5 minutes in unix/epoch time -- use for max pause time        movie_len_unix = (self.stimulus_len * 60 * 1000 * 1000) - pause_pool
        
        movie_len_unix = (self.stimulus_len * 60 * 1000 * 1000) - pause_pool
        end_time = seed + movie_len_unix 
        add_interval = int((end_time - seed) / nr_movie_frames)
        
        cpu_time = []
        for i in range(nr_movie_frames):
            seed += add_interval
            cpu_time.append(int(seed))   

        nr_pauses = int(uniform(1,3))
        min_pause = 0.1 * 1000 * 1000 * 60
        
        indices_pause = random.sample(range(len(cpu_time) - 5000), nr_pauses)
        
        cpu_time = np.array(cpu_time)
        
        for i, index in enumerate(indices_pause): 
            if (len(indices_pause) - i) > 0: 
                pause_len = random.randint(int(min_pause), pause_pool)
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
        
    def save_watchlog_with_artifacts(self) -> None:
        """Save a watchlog including pauses and skips to ``watchlogs`` dir."""
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

def run_data_generation() -> None:
    """Populate a small mock dataset and minimal annotation arrays.

    Iterates through hard-coded ``patients`` and ``sessions`` and, for each
    (patient, session) pair, uses :class:`GenerateData` to synthesize and write:
    session info, spike trains, an LFP-like channel, channel-name list, events,
    a DAQ log, and a watchlog with artifacts. After data generation, it also
    writes a few toy annotation arrays into ``PATH_TO_LABELS``.

    Steps:
        1. For each patient/session:
        - Print a short summary (:meth:`GenerateData.summarize`).
        - Save ``session_info.npy``.
        - Save spike trains (``spiking_data/*.npy``).
        - Save LFP data (``lfp_data/CSC1_lfp.npy``).
        - Save channel names (``ChannelNames.txt``).
        - Save events (``event_file/Events.npy``).
        - Save DAQ log (``daq_files/timedDAQ-log-<timestamp>.log``).
        - Save watchlog with pauses/skips (``watchlogs/ffplay-watchlog-<timestamp>.log``).
        2. Create three example ``*.npy`` annotation files under ``PATH_TO_LABELS``,
        with filenames including a random ``annotator_id`` and the current date.

    Writes:
        - Under ``{PATH_TO_DATA}/patient_data/{patient_id}/session_{session_nr}/``:
            * ``session_info.npy``
            * ``ChannelNames.txt``
            * ``spiking_data/CSC{channel}_{MU|SU}{idx}.npy``
            * ``lfp_data/CSC1_lfp.npy``
            * ``event_file/Events.npy``
            * ``daq_files/timedDAQ-log-<YYYY-mm-dd_HH-MM-SS>.log``
            * ``watchlogs/ffplay-watchlog-<YYYY-mm-dd_HH-MM-SS>.log``
        - Under ``{PATH_TO_LABELS}/``:
            * ``1_character1_<annotator_id>_<YYYYMMDD>_character.npy``
            * ``2_character2_<annotator_id>_<YYYYMMDD>_character.npy``
            * ``3_location1_<annotator_id>_<YYYYMMDD>_character.npy``

    Notes:
        - Relies on configuration/constants imported elsewhere:
        ``PATH_TO_DATA``, ``PATH_TO_LABELS``, and ``annotators``.
        - Data are randomized on each run; for reproducibility, set seeds in both
        ``random`` and ``numpy.random`` before calling.
        - Time bases follow the conventions used in :class:`GenerateData`
        (e.g., spike/event timestamps in ms, some logs in µs).

    Returns:
        None

    Example:
        run_data_generation()
    """

    patients = [1,2,3]
    sessions = [[1], [1, 2], [1]]

    print(f"Generating patient data for {len(patients)} 'patients'..")
    for patient_id, patient_sessions in zip(patients, sessions):

        for session_nr in patient_sessions:

            print(f"patient {patient_id}, session {session_nr}")

            pat_neural_data = GenerateData(patient_id, session_nr)
            pat_neural_data.summarize()
            pat_neural_data.save_session_info()

            pat_neural_data.save_spike_trains()
            pat_neural_data.save_lfp_data()
            
            pat_neural_data.save_channel_names()
            pat_neural_data.save_events()
            pat_neural_data.save_daq_log()
            pat_neural_data.save_watchlog_with_artifacts()

    print("Generating movie annotations..")

    annotator_ids = []
    for i in range(len(annotators)):
        annotator_ids.append(annotators[i]['annotator_id'])

    path = Path(PATH_TO_LABELS)
    path.mkdir(parents=True, exist_ok=True)

    start_times_1 = [0, 5000.04, 7000.04, 12000.04]
    stop_times_1 = [5000,7000,12000,12575]
    values_1 = [1,0,1,0]
    character1 = np.array([values_1, start_times_1, stop_times_1]) 
    np.save(path / f"1_character1_{random.choice(annotator_ids)}_{datetime.now().strftime('%Y%m%d')}_character.npy", character1)

    start_times_2 = [0, 400.04, 4000.04, 10000.04, 10500.04]
    stop_times_2 = [400,4000,10000,10500,12575]
    values_2 = [0,1,0,1,0]
    character2 = np.array([values_2, start_times_2, stop_times_2]) 
    np.save(path / f"2_character2_{random.choice(annotator_ids)}_{datetime.now().strftime('%Y%m%d')}_character.npy", character2)

    start_times_3 = [0, 100.04, 500.04]
    stop_times_3 = [100, 500, 12575]
    values_3 = [0,1,0]
    location1 = np.array([values_3, start_times_3, stop_times_3]) 
    np.save(path / f"3_location1_{random.choice(annotator_ids)}_{datetime.now().strftime('%Y%m%d')}_character.npy", location1)


if __name__ == "__main__":
    
    run_data_generation()