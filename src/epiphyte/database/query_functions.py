from epiphyte.database import db_setup as db


def get_patient_neural_rectime(patient_id, session_nr):
    key = dict(patient_id=patient_id, session_nr=session_nr)
    return (db.MovieSession & key).fetch1("neural_recording_time")


def get_patient_pts(patient_id, session_nr):
    key = dict(patient_id=patient_id, session_nr=session_nr)
    return (db.MovieSession & key).fetch1("pts")


def get_patient_dts(patient_id, session_nr):
    key = dict(patient_id=patient_id, session_nr=session_nr)
    return (db.MovieSession & key).fetch1("dts")


def get_start_stop_times_pauses(patient_id, session_nr):
    key = dict(patient_id=patient_id, session_nr=session_nr)
    return (db.MoviePauses & key).fetch1("start_times", "stop_times")


def get_spike_times(patient_id, session_nr, unit_id):
    key = dict(patient_id=patient_id, session_nr=session_nr, unit_id=unit_id)
    return (db.SpikeData & key).fetch1("spike_times")


def get_spike_amps(patient_id, session_nr, unit_id):
    key = dict(patient_id=patient_id, session_nr=session_nr, unit_id=unit_id)
    return (db.SpikeData & key).fetch1("spike_amps")


def get_patient_aligned_label_info(patient_id, session_nr, label_name):
    key = dict(patient_id=patient_id, session_nr=session_nr, label_name=label_name)
    return (db.PatientAlignedMovieAnnotation & key).fetch1(
        "values", "start_times", "stop_times"
    )
