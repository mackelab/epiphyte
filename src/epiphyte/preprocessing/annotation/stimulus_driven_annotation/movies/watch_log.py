"""
Watch log parsing utilities for extracting PTS and CPU timestamps.

This module provides the :class:`WatchLog` class to read a "watch log" file,
derive start/end times, and build aligned arrays/dataframes of presentation
timestamps (PTS) and real (CPU) times. It also includes helpers to trim the
recorded time series to a maximum movie duration.

Constants:
    MAX_MOVIE_TIME (int): Maximum allowable movie time (in the same units as PTS)
        used to filter out timestamps beyond the movie length.

Example:
    >>> wl = WatchLog("/path/to/watch.log")
    >>> wl.get_start_time(), wl.get_end_time()
    (12, 5012)
    >>> wl.df_pts_cpu.head()
    #    pts  cpu_time
    # 0  0.00      1234
    # 1  0.04      1270
"""
import numpy as np
import pandas as pd

MAX_MOVIE_TIME = 5029

class WatchLog:
    """
    Parse a watch log file and process the concurrent presentation time stamps (PTS) and the local PC (CPU) time series.

    On initialization, this class:
      1) Reads the provided watch log file.
      2) Extracts the start and end CPU timestamps.
      3) Loads all PTS/CPU rows, trims them to the maximum movie length, and
         converts CPU timestamps to seconds (integer, via floor division by 1000).
      4) Builds a pandas DataFrame (:attr:`df_pts_cpu`) with `pts` and `cpu_time`.

    Attributes:
        watch_log_file (str): Absolute or relative path to the watch log file.
        start_time (int): Start time in seconds (CPU time derived from the file).
        end_time (int): End time in seconds (CPU time derived from the file).
        duration (int): Duration in seconds, computed as `end_time - start_time`.
        pts_time_stamps (np.ndarray): Array of PTS values (floats), possibly trimmed.
        dts_time_stamps (np.ndarray): Array of CPU times in seconds (ints), possibly trimmed.
        excluded_indices (list[int]): Indices removed when trimming to `MAX_MOVIE_TIME`.
        df_pts_cpu (pd.DataFrame): Two-column DataFrame with `pts` and `cpu_time`.

    Notes:
        - The method :meth:`getlines` reads the log file in **binary** mode and
          returns a list of byte strings. Downstream parsing assumes whitespace-
          separated fields and converts to numeric types as needed.
        - CPU timestamps are divided by 1000 and cast to `int`, so any sub-second
          resolution is truncated rather than rounded.
    """
    def __init__(self, path_watch_log: str):
        """
        Initialize the WatchLog and populate derived fields.

        Args:
            path_watch_log (str): Path to the watch log file to load.

        Side Effects:
            - Reads the file at `path_watch_log`.
            - Populates attributes documented in the class docstring.
        """
        self.watch_log_file = path_watch_log
        self.start_time, self.end_time = self.extract_start_and_end_time()
        self.duration = self.end_time - self.start_time
        self.pts_time_stamps, self.dts_time_stamps, self.excluded_indices = self.get_times_from_watch_log(path_watch_log)
        # optionally divide time stamp by 1000 to get time in seconds
        self.dts_time_stamps = np.array([int(x / 1000) for x in self.dts_time_stamps])
        self.df_pts_cpu = pd.DataFrame({"pts": self.pts_time_stamps, "cpu_time": self.dts_time_stamps})

        self.df_pts_cpu.sort_values(['cpu_time'])

    def get_start_time(self) -> int:
        """
        Return the start CPU time (in seconds).

        Returns:
            int: Start time in seconds.
        """
        return self.start_time

    def get_end_time(self) -> int:
        """
        Return the end CPU time (in seconds).

        Returns:
            int: End time in seconds.
        """
        return self.end_time

    def _set_start_time(self, new_start_time: int):
        """
        Set a new start time (in seconds).

        Args:
            new_start_time (int): The new start time in seconds.
        """
        self.start_time = new_start_time

    def _set_end_time(self, new_end_time: int):
        """
        Set a new end time (in seconds).

        Args:
            new_end_time (int): The new end time in seconds.
        """
        self.end_time = new_end_time

    def extract_start_and_end_time(self) -> tuple[int, int]:
        """
        Extract the start and end CPU timestamps from the watch log.

        The function reads the file in text mode, takes the second line as the
        "first" data line, and scans backward from the end to find the last line
        beginning with ``"pts"``. It returns the CPU timestamps from those two
        lines, converted to seconds by dividing by 1000 and casting to `int`.

        Returns:
            tuple[int, int]: A `(start_time_s, end_time_s)` tuple in seconds.

        Raises:
            FileNotFoundError: If the watch log file cannot be opened.
            ValueError: If the file does not contain expected fields/format.
        """
        with open(self.watch_log_file, 'r') as f:
            lines = f.read().splitlines()
            first_line = lines[1]
            i = len(lines)-1
            while not lines[i].startswith("pts"):
                i -= 1
            last_line = lines[i]  # TODO change this to make it generally applicable

        # return cpu time stamp of first and last line in watch log
        # divide by 1000 to get seconds
        return int(int(first_line.split()[-1]) / 1000), int(int(last_line.split()[-1]) / 1000)

    def get_times_from_watch_log(self, path_watch_log: str) -> tuple[np.ndarray, np.ndarray, list[int]]:
        """
        Extract PTS and CPU (real) times from the watch log.

        The function reads raw lines via :meth:`getlines`, parses the whitespace-
        separated fields, and collects two arrays:
        - PTS values as floats rounded to 2 decimals.
        - CPU timestamps as integers (original units, **not** yet divided by 1000).

        It then trims both arrays to the maximum movie duration via
        :meth:`cut_time_to_movie_pts`.

        Args:
            path_watch_log (str): Path to the watch log file to parse.

        Returns:
            tuple[np.ndarray, np.ndarray, list[int]]: A tuple
            ``(pts_time_stamps, cpu_time_stamps, excluded_indices)`` where
            - `pts_time_stamps` is a float array,
            - `cpu_time_stamps` is an int array (original unit),
            - `excluded_indices` lists indices removed due to `MAX_MOVIE_TIME`.

        Raises:
            FileNotFoundError: If the watch log file cannot be opened.
            ValueError: If the log lines do not match the expected 4-field format.
        """
        lines = self.getlines(path_watch_log)
        pts = []
        time = []

        for line in lines[1:]:
            fields = line.split()
            if len(fields) == 4:
                pts.append(round(float(fields[1]), 2))
                time.append(int(fields[3]))

        pts = np.array(pts)
        time = np.array(time)

        return self.cut_time_to_movie_pts(pts, time)

    @staticmethod
    def cut_time_to_movie_pts(pts_time_stamps: np.ndarray, cpu_time_stamps: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[int]]:
        """
        Trim PTS and CPU arrays to the maximum movie length.

        Any PTS value strictly greater than :data:`MAX_MOVIE_TIME` is excluded.
        The function returns aligned arrays of the retained elements and the
        list of excluded indices.

        Args:
            pts_time_stamps (np.ndarray): Array of PTS values (floats).
            cpu_time_stamps (np.ndarray): Array of CPU times (ints), aligned with PTS.

        Returns:
            tuple[np.ndarray, np.ndarray, list[int]]: A tuple
            ``(cut_down_pts, cut_down_dts, excluded_indices)``:
            - `cut_down_pts` (np.ndarray): PTS values ≤ `MAX_MOVIE_TIME`.
            - `cut_down_dts` (np.ndarray): Corresponding CPU times.
            - `excluded_indices` (list[int]): Indices removed from the original arrays.

        Notes:
            - This function assumes `pts_time_stamps` and `cpu_time_stamps` are the
              same length and aligned 1:1.
        """
        excluded_time_points_based_on_max_movie_time = [0 if x > MAX_MOVIE_TIME else 1 for x in pts_time_stamps]

        cut_down_pts = []
        cut_down_dts = []
        excluded_indices = []
        for i in range(0, len(pts_time_stamps)):
            if excluded_time_points_based_on_max_movie_time[i] == 1:
                cut_down_pts.append(pts_time_stamps[i])
                cut_down_dts.append(cpu_time_stamps[i])
            else:
                excluded_indices.append(i)

        return np.array(cut_down_pts), np.array(cut_down_dts), excluded_indices

    @staticmethod
    def getlines(filename: str) -> list[bytes]:
        """
        Read a file in binary mode and return its lines.

        Args:
            filename (str): Path to the file to read.

        Returns:
            list[bytes]: Lines of the file as byte strings (no newline characters).

        Raises:
            FileNotFoundError: If the file cannot be opened.
        """
        with open(filename, 'rb') as logfile:
            data = logfile.read()
        lines = data.splitlines()
        return lines
