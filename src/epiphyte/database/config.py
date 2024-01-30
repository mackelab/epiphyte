"""Hard-coded variables for initializing the database"""

import os
from pathlib import Path
  
dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
PATH_TO_REPO = dir_path.parent # reduces current working directory object to just the repository location on drive.

## PATH VARIABLES 
## Note: expects existing directory structure -- configure to own data structure to adjust to 
## non-mock data sets, or place actual data into the mock_data folder and rename at will. 
PATH_TO_DATA = os.path.join(PATH_TO_REPO, "data", "mock_data")
PATH_TO_LABELS = os.path.join(PATH_TO_DATA, "movie_annotations")
PATH_PATIENT_ALIGNED_LABELS = os.path.join(PATH_TO_DATA, "patient_aligned_annotations")
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

# Example of manually setting an excluded unit
excluded_units = [
    {"patient_id": 1, "unit_id": 12, "reason_for_exclusion": "p1"}
]


patients = [
    {'patient_id': 1, 'age': 55, 'gender': 'x'},
    {'patient_id': 2, 'age': 100, 'gender': 'x'},
    {'patient_id': 3, 'age': 50, 'gender': 'x'}
]

sessions = [
    {'patient_id': 1, 'session_nr': 1, 'session_type': 'full_movie'},
    {'patient_id': 2, 'session_nr': 1, 'session_type': 'partial_movie'},
    {'patient_id': 2, 'session_nr': 2, 'session_type': 'full_movie'},
    {'patient_id': 3, 'session_nr': 1, 'session_type': 'full_movie'}
]

label_names = zip(['character1', 'character2', 'location1'])
