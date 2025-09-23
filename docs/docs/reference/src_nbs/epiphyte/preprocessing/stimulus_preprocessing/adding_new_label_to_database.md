```python
from database.db_setup import *
```

    Please enter DataJoint username:  tamara
    Please enter DataJoint password:  ·········


    Connecting tamara@localhost:3306


# Adding a new movie label to the database

### (1) Add the name of the label to 'label_names' and 'label_names_list' in 'config.py'

### (2) Make sure the new label binary is in the correct forlder on the hard drive (under /movie_labels/) and has the correct naming

### (3) Update the table "label_names" so the new label names are included:


```python
LabelName.insert(config.label_names, skip_duplicates=True)
```

### (4) Populate the table 'MovieAnnotation'

The talbe 'MovieAnnotation' depends on the table 'LabelName' and will populate with all labels that are represented in the table 'LabelName'

Check whether the label is now in the database:


```python
MovieAnnotation.populate()
```

    Added label mckenzie to database.
    Added label tom to database.
    Added label paul to database.
    Added label summer to database.
    Added label rachel to database.
    Added label mckenzie to database.
    Added label tom to database.



    ---------------------------------------------------------------------------

    KeyboardInterrupt                         Traceback (most recent call last)

    <ipython-input-3-924a25d94412> in <module>
    ----> 1 MovieAnnotation.populate()
    

    ~/miniconda3/envs/dhv_deploy/lib/python3.6/site-packages/datajoint/autopopulate.py in populate(self, suppress_errors, return_exception_objects, reserve_jobs, order, limit, max_calls, display_progress, *restrictions)
        157                     self.__class__._allow_insert = True
        158                     try:
    --> 159                         make(dict(key))
        160                     except (KeyboardInterrupt, SystemExit, Exception) as error:
        161                         try:


    ~/Documents/PhD/DeepHumanVision_deploy/database/db_setup.py in _make_tuples(self, key)
        163                 stop_times = np.array(content[2])
        164 
    --> 165                 ind_func = processing_labels.make_label_from_start_stop_times(values, start_times, stop_times, config.PTS_MOVIE_new)
        166 
        167                 self.insert1({'label_name': name,


    ~/Documents/PhD/DeepHumanVision_deploy/annotation/stimulus_driven_annotation/movies/processing_labels.py in make_label_from_start_stop_times(values, start_times, stop_times, ref_vec, default_value)
         23     for i in range(len(values)):
         24         start_index_in_default_vec = create_vectors_from_time_points.get_index_nearest_timestamp_in_vector(np.array(ref_vec), start_times[i])
    ---> 25         end_index_in_default_vec = create_vectors_from_time_points.get_index_nearest_timestamp_in_vector(np.array(ref_vec), stop_times[i])
         26 
         27         default_label[start_index_in_default_vec:(end_index_in_default_vec+1)] = \


    KeyboardInterrupt: 



```python
MovieAnnotation() & "label_name='<label_name>'"
```

### (5) Insert the new label into the table 'PatientAlignedMovieAnnotation'


```python
PatientAlignedMovieAnnotation.populate()
```


```python

```
