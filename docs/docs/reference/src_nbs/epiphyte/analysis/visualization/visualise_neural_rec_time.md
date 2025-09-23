```python
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import holoviews as hv
import panel as pn

pn.extension()
hv.extension('bokeh')

from database.db_setup import *
import database.config as config
```


```python
import param
import panel as pn

patients = config.patients
sessions = config.sessions
patient_ids = []
for patient in patients:
    patient_ids.append(patient['patient_id'])
session_nrs = [1]

class PlotterNeuralRecTime(param.Parameterized):

    patient_id = param.ObjectSelector(default=1, objects=patient_ids)
    session_nr = param.ObjectSelector(default=1, objects=session_nrs)

    @param.depends('patient_id', 'session_nr')
    def load_symbol(self):
        plot = hv.Curve(get_neural_rectime_of_patient(self.patient_id, self.session_nr)/1000, label="Neural Recording Time").opts(framewise=True, width=800, xlabel="time", ylabel="neural recording time")
        if os.path.exists("neural_rec_time.npy"):
            os.remove("neural_rec_time.npy")
        return plot
```


```python
p = PlotterNeuralRecTime()
pts_dmap = hv.DynamicMap(p.load_symbol)

pn.Column(pn.Row(pn.panel(p.param, parameters=['patient_id', 'session_nr'])), pts_dmap).servable()
```
