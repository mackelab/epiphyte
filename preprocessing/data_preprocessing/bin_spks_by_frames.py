import cv2
import os
import argparse

from data_processing import *
from binning import univ_bin


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delay', type=int, default=0, help='Delay between the na bin and frame onset (ms)')
    parser.add_argument('-b', '--binsize', type=int, default=0, help='Bin size used for binnind na (ms)')
    args = parser.parse_args()

    base_folder = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 3)

    path_events = os.path.join(base_folder, 'data/046e17mv-2015-12-12_19-10-59/Events.nev')
    path_daqlog = os.path.join(base_folder, 'code/movies_analysis/logfiles/046mv1/timedDAQ-log-20151212-193106.log')
    path_watchlog = os.path.join(base_folder, 'code/movies_analysis/logfiles/046mv1/ffplay-watchlog-20151212-193220.log')

    du = dataUnion(path_watchlog, path_daqlog, path_events, t=2, k=5)

    coeff_pts2rec, pts_start_stop = du.process_continuity()

    video_folder = os.path.join(base_folder, 'movie')
    video_path = os.path.join(video_folder, "500DaysOfSummer-Deutsch.avi")
    print(video_path)

    if not os.path.exists(os.path.normpath(video_folder + os.sep + 'frames')):
        os.mkdir(os.path.normpath(video_folder + os.sep + 'frames'))

    vidcap = cv2.VideoCapture(video_path)

    success, image = vidcap.read()
    count = 0
    frame_pts = [0]

    while success:
        pts = vidcap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # current frame pts
        # cv2.imwrite(video_folder + os.sep + 'frames' + os.sep + 'frame%d.png' % count, image)  # save frame as PNG
        frame_pts.append(pts)
        count += 1
        success, image = vidcap.read()

    for i in range(len(pts_start_stop)):
        ind_start = np.searchsorted(frame_pts, pts_start_stop[i][0])
        ind_stop = np.searchsorted(frame_pts, pts_start_stop[i][1])
        frame_rectime = coeff_pts2rec[i][:-1]*frame_pts[ind_start:ind_stop] + coeff_pts2rec[i][-1]

        rel_frames = np.array(range(ind_start, ind_stop-1))
        print(len(rel_frames))

        if args.binsize == 0:
            bin_edges = [x + args.delay for x in frame_rectime]
        else:
            bin_edges = np.zeros((ind_stop - ind_start - 1, 2))
            bin_edges[:, 0] = [x + args.delay for x in frame_rectime[:-1]]
            bin_edges[:, 1] = [x + args.delay + args.binsize for x in frame_rectime[:-1]]

        path_binaries = os.path.join(os.getcwd(), 'binaries')
        pat_id = 46
        save_dir = 'seg{0}_d{1}_b{2}'.format(i, str(args.delay), str(args.binsize))
        univ_bin(pat_id=pat_id, path_binaries=path_binaries, save_dir=save_dir, type_prefix='CSC', bins=bin_edges)
        np.save(os.path.join(path_binaries, str(pat_id), save_dir, 'relevant_frames'), rel_frames)