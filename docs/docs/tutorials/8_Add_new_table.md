# Adding Change Point Annotations to Database

### (1) Design new Table

- import necessary modules 
- think about the structure of the Table (primary keys, other keys) and the other existing Tables it might need to interact with

#### Table doc_string convention:

    class TableName(dj.TableType):
        definition = """
        # Description of Table purpose
        -> Dependency to existing Table           # Purpose of said existing Table
        primary_key: datatype                     # Purpose of primary key 
        ---
        normal_column:  datatype                  # Purpose of column (aka non-primary key) 
        """
        


```python
from database.db_setup import *

from annotation.data_driven_annotation import cpt
import preprocessing.data_preprocessing.binning as binning
import preprocessing.data_preprocessing.create_vectors_from_time_points as create_vectors_from_time_points            
```

(2) Define the Type of Table


```python
class ChangePointAnnotation(dj.Computed):
```

(3) Initialize Table



```python
class ChangePointAnnotation(dj.Computed):
    """
    # This table contains information about change points detected in spiking acitivity of single units;
    -> BinnedSpikesDuringMovie                    # the unit information and the binned spike vectors
    algorithm: varchar(32)                        # the algorithm version that was used to create the change point
    ---
    change_point: int                             # actual change point in neural recording time
    t_value: int                                  # the t-value of the test statistic
    additional_information="":varchar(32)         # space for additional information
    """
    
    def make(self, key):
        """
        Function that will run change point algorithm on spike trains and store results in database.
        """
```

(4) Define how the Table with be populated 

- write the make() function: generates the values to be put into the database
- define how those values will be inserted (order, column names, ect)


```python
class ChangePointAnnotation(dj.Computed):
    ### ask: is there a meaning to the breakpoints in the defs? 
    ### as in, above the ---, primary keys,  and below: secondary? 
    """
    # This table contains information about change points detected in spiking acitivity of single units;
    -> BinnedSpikesDuringMovie                    # the unit information and the binned spike vectors
    algorithm: varchar(32)                        # the algorithm version that was used to create the change point
    ---
    change_point: int                             # actual change point in neural recording time
    t_value: int                                  # the t-value of the test statistic
    additional_information="":varchar(32)         # space for additional information
    """
    
    def make(self, key):
        """
        Function that will run change point algorithm on spike trains and store results in database.
        """
        # Retrieve all patient id's and units that exist within the 
        # database and use for setting up the new computed table
        patient_ids, units_ids, session_nr = SpikeTimesDuringMovie().fetch("patient_id","unit_id", "session_nr")       

        for i in range(len(patient_ids)):
            pat_id = patient_ids[i]
            unit_nr = units_ids[i]
            session = session_nr[i]

            # load spike times into kernel
            unit_name = (SpikeTimesDuringMovie & "patient_id={}".format(pat_id)
                    & "unit_id={}".format(unit_nr) & "session_nr={}".format(session)).fetch("spike_times")[0]
            unit = np.load(unit_name)
            os.remove(unit_name)

            # bin spike times to 1000 msec (should this be a finer scale?)
            bin_size = 1000
            exclude_pauses = False
            output_edges = True
            binned_unit, edges = binning.bin_spikes(pat_id, session, unit, bin_size, exclude_pauses, output_edges)

            # compute change points
            # note: cpt algo auto-generates plots -- should make default not plotting for this purpose?
            tau, ttest = cpt.find_changepoint_tt(binned_unit)

            tstat = ttest[0] 
            change_point_time = [edges[tau], edges[tau+1]]

            self.insert1({"patient_id": pat_id, "unit_id": unit_nr,
                          "session_nr": session, "bin_size": bin_size,
                          "t_value": tstat, "change_point_bin": tau, "change_point_time": change_point_time})
```

(5) Populate the Table

After coding up the class, testing it, and implementing it in the db_setup.py file, add a line into the ~/database/datanase_set_up.ipynb notebook that will run and create the Table as part of the database. 


```python
# insert this line into set_up notebook
ChangePointAnnotation.populate()

# if manual Table, then would need to manually population 
# ExampleTable.insert1(to_be_inserted)
```
