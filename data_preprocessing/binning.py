import sys
import os.path
import numpy as np


def univ_bin(pat_id, path_binaries, save_dir, type_prefix, bins, rec_refs_file=None):
    """
    Universal binning function applicable to binaries, indicator fxns...
    :param pat_id : int
    Patient ID
    :param path_binaries : str
    Folder path to where activity during film binaries are
    :param save_dir : str
    Name of the folder where new files are saved
    :param type_prefix : str
    Type of file that is being binned (which determines some extra options).
    :param rec_refs_file : str
    File path to where the file with recording window is
    :param bins: int or sequence of scalars or 2d sequence of scalars
    If bins is an int, it defines the duration of each bin in msec.
    If bins is a sequence, it defines a monotonically increasing array of bin edges, including the rightmost edge,
    allowing for non-uniform bin widths.
    If bins is a 2d sequence, the second dim has to be 2 and it determines bin edges that can also overlap.
    """

    if type_prefix not in ['CSC', 'rectimes', 'scenes']:
        raise ValueError('The file_type should be either \'CSC\', \'rectimes\' or \'scenes\'.')

    bin_size = bins

    if isinstance(bins, int):
        if rec_refs_file is None:
            raise ValueError('If bin width is given, there has to be an absolute reference of time (rec_refs_file)')
        else:
            recs = np.load(os.path.join(path_binaries, str(pat_id), rec_refs_file))
            total_msec = recs[1] - recs[0]
            total_bins = int(total_msec / bins)
            bins = np.linspace(recs[0], recs[1], total_bins)

    append_name = "_bin{}.npy".format(bin_size)
    save_dir_abs = os.path.join(path_binaries, str(pat_id), save_dir)
    #if type_prefix != 'CSC':  # either rectime or scenes
    #    save_dir_abs = os.path.join(save_dir_abs, 'indicators')
    #if not os.path.exists(save_dir_abs):
    #    os.makedirs(save_dir_abs)

    for filename in os.listdir(os.path.join(path_binaries, str(pat_id))):
        if filename.startswith(type_prefix):
            binary = np.load(os.path.join(path_binaries, str(pat_id), filename))

            if type_prefix == 'scenes':
                binary = binary / 1000

            if isinstance(bins, np.ndarray) and np.ndim(bins) == 2:
                if bins.shape[1] != 2:
                    raise ValueError(
                        'If `bins` is a 2d array, the second dim has to be 2 (determines bin edges, so a pair)')
                else:
                    binary = np.asarray(binary)
                    binary = binary.ravel()
                    idxs = binary.searchsorted(bins.ravel())
                    binary_binned = np.diff(idxs)
                    binary_binned = binary_binned[0:len(binary_binned):2]
            else:
                binary_binned, _ = np.histogram(binary, bins=bins)

            name = filename[:-4] + append_name

            # this snippet is relevant for indicator functions
            if type_prefix != 'CSC':  # either rectime or scenes
                binary_binned[binary_binned > 0] = 1

            if not os.path.isfile(os.path.join(save_dir_abs, name)):
                np.save(os.path.join(save_dir_abs, name), binary_binned)
                print("{} binary successful!".format(name))
            else:
                print("{} binary exists".format(name))

    name = "bin_edges_{}".format(bin_size)
    np.save(os.path.join(save_dir_abs, name), bins)


if __name__ == '__main__':
    path_binaries = os.getcwd()
    bin_size = 500
    pat_id = 46

    univ_bin(pat_id, path_binaries, '500', 'CSC', bin_size)
