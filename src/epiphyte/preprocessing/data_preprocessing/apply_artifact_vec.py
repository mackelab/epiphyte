# 6 feb 2020, alana
# functions related to removing the artifacts that occur on a bin-level (4 std from the average spiking for the whole
# of a given recording.
# 15 may 2020 notes/update: this will likely be replaced by Marcel & Gert's work. tbd.


import os
import numpy as np

def get_art_ind(vec_art):
    """
    Load the artifact vector already made for a specific patient,
    and determine indices corresponding to the artifact/troublesome bins.

     NOTE: currently (6.feb.2020) very dependent on the point a given binary is in
            the data cleaning process. This piece of cleaning is currently configured
            to occur after data type conversion (DAQ, watchlog, ect) and before applying the
            continuous watch clipping process.

    :param vec_art: str,
        path to the artifact vector (expected to be an indicator function and binned)
    :return:
      ind_art:  array of indices corresponding to the troublesome bins
    """
    if type(vec_art) is str:
        artifacts_binned = np.load(vec_art)
    else:
        artifacts_binned = vec_art
    ind_art = np.where(artifacts_binned == 0)

    return ind_art

def remove_art_from_array(array, ind_art, save_dir=None, name=None):
    """
    Removes the troublesome/artifact bins from a given data array (spike train binary).
    Returns the cleaned binary.
    Optionally, saves the cleaned binary to directory.

    :param array: array-like,
        data to be cleaned
    :param ind_art: array-like,
        indices of the troublesome bins (generated by function, get_art_ind)
    :param save_dir: str,
        path to save directory
    :param name: str,
        name for new binary
    :return:
        array_no_art:   array with the artifact/troublesome bins removed.
    """
    array_no_art = np.delete(array, ind_art)

    if save_dir:
        append_to_name = os.path.join(name, '.npy')
        np.save(os.path.join(save_dir, append_to_name), array_no_art)

    return array_no_art

