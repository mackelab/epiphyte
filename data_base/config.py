PATH_TO_DATA = "/media/hard_drive_dhv/data_dhv"
PATH_TO_LABELS = PATH_TO_DATA + "/movie_labels"
PATH_PATIENT_ALIGNED_LABELS = PATH_TO_DATA + "/patient_aligned_labels"
PATH_TO_PATIENT_DATA = PATH_TO_DATA + "/patient_data"
PATH_TO_SESSION_DATA = PATH_TO_DATA + "/session_data"

#ROOT_FOLDER_REPOSITORY = "/home/tamara/Documents/PhD/DeepHumanVision_pilot/"

#PTS_MOVIE = [round((x * 0.04), 2) for x in range(1, 119695)]
PTS_MOVIE_new = [round((x * 0.04), 2) for x in range(1, 125725)]  # movie length: 5029 seconds (AVI file); 5029/0.04 = 125725


people = [["p1", "alana", "darcher", "lab member Alana", 'H'],
          ["p2", "poornima", "ramesh", "lab member Poornima", "H"],
          ["p5", "tamara", "mueller", "lab member Tamara", "H"],
          ["p4", "svea", "meyer", "lab member Svea", "H"],
          ["p3", "auguste", "schulz", "lab member Auguste", "H"],
          ["p6", "jan", "boltis", "lab member Jan", "H"],
          ["p7", "artur", "speiser", "lab member Artur", "H"],
          ["p8", "jakob", "macke", "lab member Jakob", "H"],
          ["p9", "janmatthis", "lueckmann", "lab member JanMatthis", "H"],
          ["p10", "carlo", "dedonno", "lab member Carlo", "H"],
          ["p11", "michael", "deistler", "lab member Michael", "H"]
          ]

annotators = [
    {'annotator_id': "p1", 'first_name': 'alana', 'last_name': 'darcher'},
    {'annotator_id': "p2", 'first_name': 'poornima', 'last_name': 'ramesh'},
    {'annotator_id': "p3", 'first_name': 'auguste', 'last_name': 'schulz'},
    {'annotator_id': "p4", 'first_name': 'svea', 'last_name': 'meyer'},
    {'annotator_id': "p5", 'first_name': 'tamara', 'last_name': 'mueller'},
    {'annotator_id': "p6", 'first_name': 'jan', 'last_name': 'boltis'},
    {'annotator_id': "p7", 'first_name': 'artur', 'last_name': 'speiser'},
    {'annotator_id': "p8", 'first_name': 'jakob', 'last_name': 'macke'},
    {'annotator_id': "p9", 'first_name': 'janmatthis', 'last_name': 'lueckmann'},
    {'annotator_id': "p10", 'first_name': 'carlo', 'last_name': 'dedonno'},
    {'annotator_id': "p11", 'first_name': 'michael', 'last_name': 'deistler'}
]

algorithms = [
    ["a1", "average", "", "Averaged labels", "A"],
    ["a2", "4stddev", "", "masking data that is greater than 4 std deviations away from mean", "A"]
]


algorithms_labels = [
    {"algorithm_name": "average", "description": "averaged labels"},
    {"algorithm_name": "4stddev", "description": "masking data that is greater then 4 std deviations away from mean"},
]

current_standard_labels = [
    {'label_id': 1},
    {'label_id': 2},
    {'label_id': 3},
    {'label_id': 4},
    {'label_id': 5},
    {'label_id': 6},
    {'label_id': 9},
    {'label_id': 10},
]


excluded_units = [
    {"patient_id": 46, "unit_id": 52, "reason_for_exclusion": "p1"}
]


patients = [
    {'patient_id': 46, 'age': 1, 'gender': 'f', 'year': 2015, 'removed_tissue': "unknown", "epilepsy_type": "unknown"},
    {'patient_id': 50, 'age': 1, 'gender': 'x', 'year': 2016, 'removed_tissue': "unknown", 'epilepsy_type': "unknown"},
    {'patient_id': 52, 'age': 1, 'gender': 'x', 'year': 2016, 'removed_tissue': "unknown", "epilepsy_type": "unknown"},
    {'patient_id': 53, 'age': 1, 'gender': 'x', 'year': 2016, 'removed_tissue': "unknown", "epilepsy_type": "unknown"},
    {'patient_id': 60, 'age': 1, 'gender': 'x', 'year': 2017, 'removed_tissue': "unknown", "epilepsy_type": "unknown"},
]

watchlog_names = {46: "ffplay-watchlog-20151212-193220.log",
                  50: "ffplay-watchlog-20160502-211109.log",
                  52: "ffplay-watchlog-20160513-182133.log",
                  53: "ffplay-watchlog-20160601-205153.log",
                  60: "ffplay-watchlog-20170320-191156.log",
                  }

daq_names = {46: 'timedDAQ-log-20151212-193106.log',
             50: "timedDAQ-log-20160502-211024.log",
             52: "timedDAQ-log-20160513-182025.log",
             53: "timedDAQ-log-20160601-205121.log",
             60: "timedDAQ-log-20170320-190723.log",
            }

label_names = zip(['tom', 'summer', 'rachel', 'test', 'mckenzie', 'paul', 'happy', 'sad', 'angry', 'work', 'ikea',
                   'tomsapartment', 'summersapartment', 'bar', 'recordstore', 'park', 'restaurant',
                   'interstitialscreens', 'identicalscenesummer', 'tomonset', 'summeronset', 'paulonset', 'rachelonset',
                   'mckenzieonset', 'vorspann', 'abspann', 'kidssegment'])

label_names_list = ['tom', 'summer', 'rachel', 'mckenzie', 'paul', 'happy', 'sad', 'angry', 'work', 'ikea',
                   'tomsapartment', 'summersapartment', 'bar', 'recordstore', 'park', 'restaurant',
                   'interstitialscreens', 'identicalscenesummer', 'tomonset', 'summeronset', 'paulonset', 'rachelonset',
                   'mckenzieonset', 'vorspann', 'abspann', 'kidssegment']