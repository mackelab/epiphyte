## 5 feb 2020, alana
## functions for clipping a binary/spike train to a continuous watch indicator vector

import numpy as np
import os

def clip_array(unit, cont_watch):
    """
    Applies the continuous watch vector to a spike train to pare down the activity binary for further analysis.

    :param unit: array,
        spike train/binary
    :param cont_watch: array,
        indicator function for continuous watch of a given patient
    :return:
        clipped_array:
            array with only the activity points which occur during the continuous act. vector
        ind_clipped_array:
            original indices of the clipped_array data points
        removed_bins:
            array with the activity points that occurred outside the continuous act. vector
        ind_removed_bins:
            original indices of the removed_bins data points
    """
    # activity is separated into "to be used" (clipped array) and "not to be used" (removed bins)
    clipped_array = []
    removed_bins = []

    # indices for the activity bins, for the respective separations
    ind_clipped_array = []
    ind_removed_bins = []

    for i, value in enumerate(cont_watch):
        if value == 1:
            clipped_array.append(unit[i])
            ind_clipped_array.append(i)
        if value == 0:
            removed_bins.append(unit[i])
            ind_removed_bins.append(i)

    return clipped_array, ind_clipped_array, removed_bins, ind_removed_bins

def clip_binaries(cont_watch, path_binaries, save_dir, file_key='CSC'):
    """
    Iterates through directory with spike data and pares binaries down to just the activity
    that occurs during the continuous watch portion.
    Saves new, clipped activity binaries.

    NOTE: (6.feb.2020) perhaps might be unnecessary function if we restructure
            the data cleaning procedure away from iterating over stuff over and over, for each step.

    :param cont_watch: array,
        indicator function of cont. play
    :param path_binaries: str,
        path to the original spiking activity
    :param save_dir: str,
        path to the place to save
    :param file_key: str,
        determines the files withing the directory to be analysed
        default: 'CSC'
    """
    for filename in os.listdir(path_binaries):
        if filename.startswith(file_key):
            unit = np.load(os.path.join(path_binaries, filename))

            clipped_array, _, _, _ = clip_array(unit, cont_watch)

            name = filename[:-4] + "_clipped.npy"
            np.save(os.path.join(save_dir, name), clipped_array)

