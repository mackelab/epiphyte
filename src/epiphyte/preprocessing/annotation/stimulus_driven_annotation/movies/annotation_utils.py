"""Helpers for handling stimulus-driven annotations in an analysis workflows.

Provides utilities to split neural activity by label values for downstream
analysis and visualization.
"""

import sys
from typing import Dict, Iterable, List, Optional
from types import SimpleNamespace

import numpy as np
import inflect

# Local application imports 
from database.db_setup import *
import preprocessing.data_preprocessing.binning as binning
import preprocessing.data_preprocessing.create_vectors_from_time_points as create


# split activity based on condition 

def split_activity_by_value(
    binned_activity: np.ndarray,
    binned_label: np.ndarray,
    specific_values: Optional[Iterable[int]] = None,
) -> Dict[str, np.ndarray]:
    """Split binned activity by the values in a binned label vector.

    Example:
        For a binary label (stimulus on/off), the ``binned_label`` vector
        contains 0/1. This function returns two arrays mapping to segments
        where the label is off/on, respectively. For multi-valued labels,
        activity is split per unique value.

    Args:
        binned_activity (np.ndarray): Binned neural activity (shape ``(N, ...)``).
        binned_label (np.ndarray): Binned label aligned to the activity (length ``N``).
        specific_values (Optional[Iterable[int]]): If provided, only these label values are used.
        
    Returns:
        Dict[str, np.ndarray]: Mapping ``{value_name: activity_subset}``.
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