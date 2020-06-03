import os

PATH_TO_REPO = "/home/hitchhiker/Documents//DeepHumanVision_deploy"
PATH_TO_DATA = os.path.join(PATH_TO_REPO, "mock_data") 
PATH_TO_LABELS = os.path.join(PATH_TO_DATA, "movie_labels")
PATH_PATIENT_ALIGNED_LABELS = os.path.join(PATH_TO_DATA, "patient_aligned_labels")
PATH_TO_PATIENT_DATA = os.path.join(PATH_TO_DATA, "patient_data")
PATH_TO_SESSION_DATA = os.path.join(PATH_TO_DATA, "session_data")


PTS_MOVIE_new = [round((x * 0.04), 2) for x in range(1, 125726)]  # movie length: 5029 seconds (AVI file); 5029/0.04 = 125725

annotators = [
    {'annotator_id': "p1", 'first_name': 'max', 'last_name': 'mustermann'},
    {'annotator_id': "p2", 'first_name': 'susi', 'last_name': 'lastname'},
]

algorithms = [
    ["a1", "average", "", "Averaged labels", "A"],
    ["a2", "4stddev", "", "masking data that is greater than 4 std deviations away from mean", "A"]
]


algorithms_labels = [
    {"algorithm_name": "average", "description": "averaged labels"},
    {"algorithm_name": "4stddev", "description": "masking data that is greater then 4 std deviations away from mean"},
]

excluded_units = [
    {"patient_id": 60, "unit_id": 52, "reason_for_exclusion": "p1"}
]


patients = [
    {'patient_id': 60, 'age': 1, 'gender': 'x', 'year': 2017, 'removed_tissue': "unknown", "epilepsy_type": "unknown"},
]

sessions = {
    "60": [1],
}

watchlog_names = {
                  60: "ffplay-watchlog-20170101-120000.log",
                  }

daq_names = {
             60: "timedDAQ-log-20170101-120000.log",
            }

label_names = zip(['character1', 'character2', 'location1'])
