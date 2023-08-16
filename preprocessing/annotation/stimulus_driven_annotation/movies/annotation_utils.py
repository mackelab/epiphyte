"""
General purpose functions for handling stimulus driven annotations, especially as it concerns analysis. 
"""

import sys

from types import SimpleNamespace
import inflect

# Local application imports 
from database.db_setup import *
import preprocessing.data_preprocessing.binning as binning
import preprocessing.data_preprocessing.create_vectors_from_time_points as create


# split activity based on condition 

def split_activity_by_value(binned_activity, binned_label, specific_values=None):
    """
    This function splits the spiking activity into separate vectors based on the values of the binned label. 
    
    Example: for a binary label (stimulus on/off), the binned_label vector consists of 1's and 0's. This function splits
            the activity into two vectors, each consisting of the activity that corresponds to the stimulus-on (1) or the stimulus-off (0).
             
            For a multi-values label (e.g., continuous watch label with a few different segements), will split based on each value. 
            
    If specific values are given, the function will only isolate the activity which corresponds to those values, and ignore the others. 
    
    Inputs:
    binned_activity: binned neural activity (array-like)
    binned_label: binned label, created using the reference vector of the activity (array-like)
    specific_values: Optional, if given, the function will only consider these values of the binned label 
    
    Outputs: 
    ret_vectors: dictionary of neural activity that occurred separated according to the values of the label (dict)
    
    """
    # Set up for number --> word converstion 
    alph = inflect.engine()
    
    if not specific_values: 
        values = np.unique(binned_label)
        
        ret_vectors = {}
        
        for value in values:
            
            indices = np.isin(binned_label, value)
            activity_from_val = binned_activity[indices]
            
            # Convert value number to the word, for easy referencing during analysis
            name = alph.number_to_words(int(value))
            
            ret_vectors[name] = activity_from_val
            
    if specific_values: 
        
        ret_vectors = {}
        
        for value in specific_values:
            indices = np.isin(binned_label, value)
            activity_from_val = binned_activity[indices]
            
            name = alph.number_to_words(int(value))
            ret_vectors[name] = activity_from_val
            
    return ret_vectors