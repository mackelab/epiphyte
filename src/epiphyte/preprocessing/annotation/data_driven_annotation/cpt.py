"""Detects the changepoint in a spike train using parametric statistic testing.

Plots the results and returns the index of the breakpoint and the stat test results.

Used for demonstrating the addition of a new table to an existing database. 
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

def find_changepoint_tt(data, verbose=False):
    """
    Detects the changepoint in a spike train using parametric statistic testing.
    Plots the results and returns the index of the breakpoint and the stat test results.

    Accepts and runs one unit. Set up to be iterated over for the whole of a dataset of units.

    Args:
        data (np.ndarray):  spike train data (1D array-like)
        verbose (bool):    if True, prints detailed changepoint and t-test results
        
    Returns:
        taustar (int): index of the determined breakpoint.
        ttest (stats.ttest_ind_from_stats): results from the scipy stats ttest (type is a specific class construction from scipy)
    """
    n = len(data)
    
    mu0 = np.mean(data)  # global mean
    s0 = np.sum((data - mu0) ** 2)  # squared difference from global mean
    s1 = np.asarray(
        [np.sum((data[0:i] - np.mean(data[0:i])) ** 2) for i in range(1, n)])  # squared sum before changepoint
    s2 = np.asarray(
        [np.sum((data[i:] - np.mean(data[i:])) ** 2) for i in range(1, n)])  # squared sum after changepoint

    R = s0 - s1 - s2
    G = np.max(R)

    taustar = int(np.where(R == G)[0]) + 1

    m1 = np.mean(data[0:taustar])
    std1 = np.std(data[0:taustar])
    nobs1 = len(data[0:taustar])
    m2 = np.mean(data[taustar:])
    std2 = np.std(data[taustar:])
    nobs2 = len(data[taustar:])

    ttest = stats.ttest_ind_from_stats(m1, std1, nobs1, m2, std2, nobs2)

    if verbose:
        print("Changepoint results:")
        print("tau*: ", taustar)
        print("mean pre-tau: ", m1)
        print("std  pre-tau: ", std1)
        print("mean post-tau: ", m2)
        print("std  post-tau:", std2)
        print("T-test results:")
        print(ttest)
        print("")

    return taustar, ttest

def plot_changepoint(data, taustar, ttest, save=None, filename=None, comparison_tau=None):
    """
    Plot a change point in neural activity data and annotate with statistical results.

    This function visualizes time-binned neural activity and overlays vertical
    lines indicating the detected change point (`taustar`) and, optionally, a
    second change point (`comparison_tau`). It also displays the results of a
    t-test as legend entries.

    Args:
        data (array-like): 
            Sequence of neural activity values.
        taustar (int): 
            Detected change point index (in 1-second bins).
        ttest (tuple): 
            A tuple containing (t-statistic, p-value) from a t-test.
        save (str, optional): 
            Directory path where plots should be saved. If None, plots are not saved.
        filename (str, optional): 
            Base filename (without extension) for saving plots. Required if `save` is provided.
        comparison_tau (int, optional): 
            Another change point index to compare with `taustar`.

    Returns:
        None

    Saves:
        - `{filename}_cpt.png` in the `save` directory if `save` is provided.
        - `{filename}_cpt.svg` in the `save` directory if `save` is provided.

    Example:
        ```python
        from scipy.stats import ttest_ind

        data = [0, 1, 2, 5, 6, 7, 10, 11]
        ttest = ttest_ind(data[:4], data[4:])
        plot_changepoint(data, taustar=4, ttest=ttest, save="plots/", filename="session1")
        ```
    """
    n = len(data)
    fig = plt.figure(figsize=(25, 5))
    plt.plot(np.arange(1, n + 1), data)
    plt.axvline(x=taustar, color='r', label="tau: {}".format(taustar))

    if comparison_tau:
        # note: comparison_tau is expected to be an int type value from a previously computed set of cpt results
        plt.axvline(x=comparison_tau, color='y', label="other tau: {}".format(comparison_tau))

    pval_str = "P-value: {}".format(ttest[1])
    tstat_str = "T-statistic: {}".format(ttest[0])
    plt.plot([], [], "", label=pval_str)
    plt.plot([], [], "", label=tstat_str)
    plt.xlabel('Time [1 sec bins]')
    plt.ylabel('Neural Activity [spikes / bin]')
    plt.legend(prop={'size': 15})

    if save:
        plt.title(filename + ' change point statistics')

        plt.savefig(save + "{}_cpt.png".format(filename), bbox_inches='tight')
        plt.savefig(save + "{}_cpt.svg".format(filename), format='svg', bbox_inches='tight')

    plt.show()
