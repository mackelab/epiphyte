## 5 feb 2020, script with change point detection functions.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

import sys
import os.path


def find_changepoint_tt(data, save=None, filename=None, comparison_tau=None):
    """
    Detects the changepoint in a spike train using parametric statistic testing.
    Plots the results and returns the index of the breakpoint and the stat test results.

    Accepts and runs one unit. Set up to be iterated over for the whole of a dataset of units.

    Note: forces a breakpoint, and only a single breakpoint.

    :param data: array,
        spike train/unit binary
    :param save: str,
        path to save directory
    :param filename: str,
        filename for saving, ideally the unit name
    :param comparison_tau: int,
        tau value for the given unit from another cpt run
    :return:
        taustar: index of the determined breakpoint.
        ttest:  results from the scipy stats ttest (type is a specific class construction from scipy)
    """
    n = len(data)
    tau = np.arange(1, n)

    mu0 = np.mean(data)  # global mean
    s0 = np.sum((data - mu0) ** 2)  # squared difference from global mean
    s1 = np.asarray(
        [np.sum((data[0:i] - np.mean(data[0:i])) ** 2) for i in range(1, n)])  # squared sum before changepoint
    s2 = np.asarray(
        [np.sum((data[i:] - np.mean(data[i:])) ** 2) for i in range(1, n)])  # squared sum after changepoint

    R = s0 - s1 - s2
    G = np.max(R)

    taustar = int(np.where(R == G)[0]) + 1

    print("tau: ", taustar)

    # global
    m0 = np.mean(data)
    std0 = np.std(data)

    m1 = np.mean(data[0:taustar])
    std1 = np.std(data[0:taustar])
    nobs1 = len(data[0:taustar])
    m2 = np.mean(data[taustar:])
    std2 = np.std(data[taustar:])
    nobs2 = len(data[taustar:])

    print("mean pre-tau: ", m1)
    print("std  pre-tau: ", std1)
    print("mean post-tau: ", m2)
    print("std  post-tau:", std2)

    print("")
    print("T-tests:")
    # does it make sense to use this test statistic, since it assumes independence.. even though it calcs based on descriptive stats?
    ttest = stats.ttest_ind_from_stats(m1, std1, nobs1, m2, std2, nobs2)
    print("2tail, pre- to post-tau", ttest[1])
    print("2tail, pre- to post-tau", ttest[0])

    print("")

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

    return taustar, ttest

def tidy_results(pvals, tstat, names, taus):
    """
    For use in the function, run_cpt_tt.
    Purpose: after running the change point detection analysis, puts the results into a pandas dataframe for readability

    :inputs: inherits from run_cpt_tt output

    :return:
        pandas df
        [unit, tau, pvals, tstat_raw, tstat_abs]
    """
    results = pd.DataFrame()
    results['unit'] = names
    results['tau'] = taus
    results['pvals'] = pvals
    results['tstat_raw'] = tstat
    results['tstat_abs'] = np.abs(tstat)


def run_cpt_tt(directory, save=None, file_key='CSC'):
    """
    Runs change point detection function over all units in a given directory and collects the results.


    :param directory: str,
        path leading to the folder containing the units to be analysed
    :param save: str,
        save path
    :param file_key: str,
        determines the files withing the directory to be analysed
        default: 'CSC'
    :return:
        pvals:
            p-value of the scipy tt test
        tstat:
            t-statistic
        names:
            name of the unit
            NOTE: set for bin1000 -- if using bin with more/fewer digits, will need to change to be pretty
        taus:
            taus, aka indices of the breakpoints in the spike train

    """
    pvals = []
    tstat = []
    names = []
    taus = []

    for filename in os.listdir(directory):
        if filename.startswith(file_key):
            unit = np.load(directory + filename)

            # TODO generalize filename aspects of the saving.
            name = filename[:-24]

            tau, ttest = find_changepoint_tt(unit, save=save, filename=name)

            pvals.append(ttest[1])
            tstat.append(ttest[0])
            names.append(name)
            taus.append(tau)

    return pvals, tstat, names, taus

