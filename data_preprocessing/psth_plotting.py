# Refractored 28.11.19 to account for the change in the binner (modified to work with Alek's code)
# essentially, wrapper for plotting PSTH 

import sys
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

bin_path = "../../data_preprocessing/"
sys.path.append(bin_path)
import os.path
from binning import univ_bin


class PSTH:
    def __init__(self, patient_id, bin_size, path_to_raw_spikes='../../data_preprocessing/binaries/',
                 path_to_raw_cut_times='../../data_preprocessing/binaries/'):
        """
        """
        self.patient_id = patient_id
        self.bin_size = bin_size

        # Default values, based on structure of project file.
        self.path_to_raw_spikes = path_to_raw_spikes  # path to raw binaries of spikes
        self.path_to_raw_cut_times = path_to_raw_cut_times

    def bin_spikes_and_cuts(self, rec_refs):
        """
        Uses imported binning module to bin spikes and cuts according to bin-size
        Bin size ==> expects milliseconds.
        TODO fix this so that  it works with the new binner
        :return:
        """
        save_dir = self.path_to_raw_cut_times + "{}/{}/indicators/scenes_pyscene_t_{}_bin{}.npy".format(self.patient_id,
                                                                                                        self.bin_size,
                                                                                                        self.patient_id,
                                                                                                        self.bin_size)

        univ_bin(self.patient_id, self.path_to_raw_spikes, save_dir, 'scenes', self.bin_size, rec_refs)

    def load_and_check_cuts(self):
        """
        Compare the number of 'raw' cuts seen by the patient to those in the binned version.
        Path used to load cuts_binned comes from Binning module. Take care in case of refractoring.
        :return:
        """
        cuts_binned = np.load(
            self.path_to_raw_cut_times + "{}/{}/indicators/scenes_pyscene_t_{}_bin{}.npy".format(self.patient_id, self.bin_size, self.patient_id,
                                                                                                      self.bin_size))
        raw_cuts = np.load(self.path_to_raw_cut_times + "{}/scenes_pyscene_t_{}.npy".format(self.patient_id, self.patient_id))
        print("len raw cuts: {}".format(len(raw_cuts)))
        print("sum bin cuts: {}".format(sum(cuts_binned)))
        print("These values need to be the same. If binned is zero, raw_cuts are likely in microseconds. ")
        print("Note: for larger bin sizes (e.g., second long), these values may be slightly different.")
        print(
            "Some 'scenes' are super short, and binning at larger interval collapses multiple scenes into single scene marker.")

    def make_plot_indices(self, seconds_prior, seconds_after):
        """
        Calculate indices needed for plotting PSTH, based on the bin size and the number of seconds before/after to plot.
        :param seconds_prior: int, seconds prior to stimulus to plot
        :param seconds_after: int, seconds post stim to plot
        :return:
            pre_spacer: number of indices prior to include in plot
            post_spacer: same, for after stim
            labels: x-axis labels for PSTH plot
        """
        pre_spacer = (seconds_prior * 1000) / self.bin_size
        post_spacer = (seconds_after * 1000) / self.bin_size

        pre_spacer = int(pre_spacer)
        post_spacer = int(post_spacer)

        pre_labels = np.arange((-1 * pre_spacer), 0, 1)
        post_labels = np.arange(0, post_spacer + 1, 1)
        labels = np.concatenate((pre_labels,post_labels))
        return pre_spacer, post_spacer, labels

    def plot_psth(self, seconds_prior, seconds_after, indic_path=None, raw_spikes_path=None, heat_scale=None, save_path=None, plot_sum=True):
        """
        Plots psth for desired parameters, for all cells of a given patient.
        :param plot_sum: if True, plots the sum of spikes over the specified time course.
        :param save_path: if None, no saving. If you want to save, put a file path here. Will save all plots there, in svg form.
        :param seconds_prior: int, seconds before stimulus onset to plot
        :param seconds_after: int, seconds after stimulus onset to plot
        :param heat_scale: tuple, (vmin, vmax), for making heatmaps be on the same scale across units
        :return: plots!
        """
        if indic_path:
            cuts_binned = np.load(indic_path)
        else:
            cuts_binned = np.load(
                self.path_to_raw_cut_times + "{}/{}/indicators/scenes_pyscene_t_{}_bin{}.npy".format(self.patient_id,
                                                                                                      self.bin_size,
                                                                                                      self.patient_id,
                                                                                                    self.bin_size))
        if raw_spikes_path:
            spike_path = raw_spikes_path
        else:
            spike_path = self.path_to_raw_spikes + "{}/{}/".format(self.patient_id, self.bin_size)


        pre_spacer, post_spacer, labels = self.make_plot_indices(seconds_prior, seconds_after)

        cuts_ind = np.where(cuts_binned)[0]

        for filename in os.listdir(spike_path):
            if filename.startswith('CSC'):
                unit = np.load(spike_path + filename)
                pre_stim = []
                post_stim = []
                both_stim = []

                for i, ind in enumerate(cuts_ind):
                    pre = ind - pre_spacer
                    post = ind + post_spacer

                    pre_stim.append(unit[pre:ind])
                    post_stim.append(unit[ind:post])
                    both_stim.append(unit[pre:post])

                plt.figure(figsize=(10, 10))

                if heat_scale is None:
                    ax = sns.heatmap(both_stim, cmap="vlag", center=0, cbar_kws={'label': 'Firing Rate (Hz)'})
                    ax.figure.axes[-1].yaxis.label.set_size('x-large')

                    cax = plt.gcf().axes[-1]
                    cax.tick_params(labelsize='x-large')
                else:
                    ax = sns.heatmap(both_stim, cmap="vlag", center=0, cbar_kws={'label': 'Firing Rate (Hz)'},
                                                                                 vmin=heat_scale[0], vmax=heat_scale[1])

                plt.axvline(x=pre_spacer)
                plt.title("PSTH, unit {}".format(filename[:-4]))
                plt.ylabel("'Scene' Number", fontsize='x-large')

                ax_len = int(pre_spacer + post_spacer + 1)

                plt.xticks(range(0, ax_len), labels, fontsize='x-large')

                for label in ax.xaxis.get_ticklabels()[::1]:
                    label.set_visible(False)

                for label in ax.xaxis.get_ticklabels()[::10]:
                    label.set_visible(True)
                plt.xlabel("Time surrounding stimulus, {}ms increments".format(self.bin_size), fontsize='x-large')

                plt.yticks(fontsize='x-large')
                for label in ax.yaxis.get_ticklabels()[::1]:
                    label.set_visible(False)

                for label in ax.yaxis.get_ticklabels()[::10]:
                    label.set_visible(True)


                if save_path is not None:
                    plt.savefig(save_path + '{}_psth.png'.format(filename[:-4]), bbox_inches='tight')
                    plt.savefig(save_path + '{}_psth.svg'.format(filename[:-4]), bbox_inches='tight')
                if plot_sum is True:
                    line_labels = np.delete(labels, np.where(labels == 0))

                    sum_pre = []
                    for x in range(pre_spacer):
                        segment = []
                        for p, cut in enumerate(pre_stim):
                            segment.append(cut[x])
                        sum_pre.append(sum(segment))

                    sum_post = []
                    for x in range(post_spacer):
                        segment = []
                        for p, cut in enumerate(post_stim):
                            segment.append(cut[x])
                        sum_post.append(sum(segment))

                    line_data = pd.DataFrame({'Time': line_labels, 'sum_firing_rate': np.concatenate((sum_pre, sum_post))})
                    plt.figure(figsize=(8, 3))

                    avg_FR_str = "Avg. FR prior: {}, Avg. FR post: {}".format(int(np.mean(sum_pre)), int(np.mean(sum_post)))



                    ax2 = sns.lineplot(x="Time", y='sum_firing_rate', data=line_data, color='black', label=avg_FR_str)

                    plt.axvline(x=0)
                    ax2.set_xlim([line_labels[0],line_labels[-1]])
                    plt.xlabel("Time surrounding stimulus, {}ms increments".format(self.bin_size), fontsize='x-large')
                    plt.xticks(fontsize='x-large')
                    plt.yticks(fontsize='x-large')
                    plt.ylabel("Summed firing rate",fontsize='x-large')

                    plt.legend(frameon=False)
                    if save_path is not None:
                        plt.savefig(save_path + '{}_sumFR.svg'.format(filename[:-4]),
                                    bbox_inches='tight')
                        plt.savefig(save_path + '{}_sumFR.png'.format(filename[:-4]),
                                    bbox_inches='tight')
                plt.show()

    def plot_psth_by_unit(self, unit_name, seconds_prior, seconds_after, heat_scale=None, save_path=None, plot_sum=True):
        cuts_binned = np.load(
            self.path_to_raw_cut_times + "{}/{}/indicators/scenes_pyscene_t_{}_bin{}.npy".format(self.patient_id,
                                                                                                 self.bin_size,
                                                                                                 self.patient_id,
                                                                                                 self.bin_size))

        pre_spacer, post_spacer, labels = self.make_plot_indices(seconds_prior, seconds_after)

        cuts_ind = np.where(cuts_binned)[0]


        for filename in os.listdir(self.path_to_raw_spikes + "{}/{}/".format(self.patient_id, self.bin_size)):
            if filename.startswith(unit_name):
                unit = np.load(self.path_to_raw_spikes + "{}/{}/".format(self.patient_id, self.bin_size) + filename)
                pre_stim = []
                post_stim = []
                both_stim = []

                for i, ind in enumerate(cuts_ind):
                    pre = ind - pre_spacer
                    post = ind + post_spacer

                    pre_stim.append(unit[pre:ind])
                    post_stim.append(unit[ind:post])
                    both_stim.append(unit[pre:post])

                plt.figure(figsize=(10, 10))

                if heat_scale is None:
                    ax = sns.heatmap(both_stim, cmap="vlag", center=0, cbar_kws={'label': 'Firing Rate (Hz)'})
                else:
                    ax = sns.heatmap(both_stim, cmap="vlag", center=0, cbar_kws={'label': 'Firing Rate (Hz)'},
                                                                                 vmin=heat_scale[0], vmax=heat_scale[1])

                plt.axvline(x=pre_spacer)
                plt.title("PSTH, unit {}".format(filename[:-4]))
                plt.ylabel("'Scene' Number")

                ax_len = int(pre_spacer + post_spacer + 1)

                plt.xticks(range(0, ax_len), labels)
                plt.xlabel("Time surrounding stimulus, {}ms increments".format(self.bin_size))

                if save_path is not None:
                    plt.savefig(save_path + '{}_psth'.format(filename[:-4]), format='svg', bbox_inches='tight')

                if plot_sum is True:
                    line_labels = np.delete(labels, np.where(labels == 0))

                    sum_pre = []
                    for x in range(pre_spacer):
                        segment = []
                        for p, cut in enumerate(pre_stim):
                            segment.append(cut[x])
                        sum_pre.append(sum(segment))

                    sum_post = []
                    for x in range(post_spacer):
                        segment = []
                        for p, cut in enumerate(post_stim):
                            segment.append(cut[x])
                        sum_post.append(sum(segment))

                    line_data = pd.DataFrame({'Time': line_labels, 'sum_firing_rate': np.concatenate((sum_pre, sum_post))})
                    plt.figure(figsize=(8, 3))

                    avg_FR_str = "Avg. FR prior: {}, Avg. FR post: {}".format(np.mean(sum_pre), np.mean(sum_post))



                    ax2 = sns.lineplot(x="Time", y='sum_firing_rate', data=line_data, color='black', label=avg_FR_str)

                    plt.axvline(x=0)
                    ax2.set_xlim([line_labels[0],line_labels[-1]])
                    plt.xlabel("Time surrounding stimulus, {}ms increments".format(self.bin_size))

                    plt.legend()
                    if save_path is not None:
                        plt.savefig(save_path + '{}_sumFR'.format(filename[:-4]), format='svg',
                                    bbox_inches='tight')
                plt.show()

if __name__ == "__main__":
    pat_id = 46
    bin_size = 100
    psth = PSTH(pat_id, bin_size)

    psth.load_and_check_cuts()
    psth.plot_psth(2,3,plot_sum=True)
