import numpy as np
import pandas as pd

MAX_MOVIE_TIME = 5029


class WatchLog:

    def __init__(self, path_watch_log):
        self.watch_log_file = path_watch_log
        self.start_time, self.end_time = self.extract_start_and_end_time()
        self.duration = self.end_time - self.start_time
        self.pts_time_stamps, self.dts_time_stamps, self.excluded_indices = self.get_times_from_watch_log(path_watch_log)
        # optionally divide time stamp by 1000 to get time in seconds
        self.dts_time_stamps = np.array([int(x / 1000) for x in self.dts_time_stamps])
        self.df_pts_cpu = pd.DataFrame({"pts": self.pts_time_stamps, "cpu_time": self.dts_time_stamps})

        self.df_pts_cpu.sort_values(['cpu_time'])

    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time

    def _set_start_time(self, new_start_time):
        self.start_time = new_start_time

    def _set_end_time(self, new_end_time):
        self.end_time = new_end_time

    def extract_start_and_end_time(self):

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

    def get_times_from_watch_log(self, path_watch_log):
        """
        Extracts pts and real times (CPU times) from watch log
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
    def cut_time_to_movie_pts(pts_time_stamps, cpu_time_stamps):
        """
        Cutting pts and cpu time stamps to a maximum of the movie length
        :return: new_pts_time: list of pts time stamps that are smaller than MAX_MOVIE_TIME
                 new_cpu_time: list of corresponding cpu times
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
    def getlines(filename):
        with open(filename, 'rb') as logfile:
            data = logfile.read()
        lines = data.splitlines()
        return lines
