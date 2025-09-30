"""Helper functions used in the `database` module.

This module provides small utilities for parsing filenames, sorting keys
in a human-friendly way, and extracting metadata encoded in strings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, Union

import numpy as np


def atoi(text: str) -> Union[int, str]:
    """Convert a numeric substring to ``int`` or return the original string.

    Args:
        text (str): Substring that may contain only digits.

    Returns:
        Union[int, str]: Integer value (if all digits) or the original string.
    """

    return int(text) if text.isdigit() else text


def natural_keys(text: str) -> List[Union[int, str]]:
    """Split a string into chunks for human (natural) sorting.

    Use as ``alist.sort(key=natural_keys)`` to sort filenames such as
    ``CSC2_SU1.npy`` before ``CSC10_SU1.npy``.

    Notes:
        Based on Ned Batchelder's human sorting recipe.

    Args:
        text (str): Input string to split into text and integer chunks.
    
    Returns:
        List[Union[int, str]]: Alternating text and integer parts suitable as a sort key.
    """

    return [atoi(chunk) for chunk in re.split(r"(\d+)", text)]


def extract_sort_key(filename: str) -> Union[Tuple[int, str, int], str]:
    """Extract a sortable key from a spike filename.

    Filenames are expected to follow ``CSC<nr>_<type><nr>.npy``. If the
    pattern matches, returns a tuple ``(csc_number, unit_type, unit_nr)``.
    Otherwise, returns the original filename for fallback sorting.

    Args:
        filename (str): Filename to parse.

    Returns:
        Union[Tuple[int, str, int], str]: Tuple for sorting or the original filename.
    """

    match = re.match(r"CSC(\d+)_(\w+)(\d*)\.npy", filename)
    if match:
        csc_number = int(match.group(1))
        mu_su = match.group(2)
        mu_su_number = int(match.group(3)) if match.group(3) else 0
        return csc_number, mu_su, mu_su_number
    return filename


def get_channel_names(path_channel_names: Union[str, Path]) -> List[str]:
    """Read channel names (without extensions) from a text file.

    The file is expected to contain lines like ``<name>.ncs``. The suffix is
    stripped to yield bare channel identifiers.

    Args:
        path_channel_names (Union[str, Path]): Path to the channel names file.

    Returns:
        List[str]: List of channel name strings.
    """

    channel_names: List[str] = []
    with open(path_channel_names, "r") as handle:
        for line in handle:
            # Strip trailing "\n" and ".ncs" (5 chars), keep the base name only.
            channel_names.append(line[:-5 - 1])
    return channel_names


def get_unit_type_and_number(unit_string: str) -> Tuple[str, str]:
    """Parse a unit string into unit type and number.

    Example: ``CSC_MUA1`` -> ("M", "1").

    Args:
        unit_string (str): Original unit string (e.g., ``"MUA1"`` or ``"SU3"``).

    Returns:
        Tuple[str, str]: Tuple ``(unit_type, unit_nr)`` where type is ``"M"``, ``"S"``, or ``"X"``.
    """

    if "MU" in unit_string:
        unit_type = "M"
    elif "SU" in unit_string:
        unit_type = "S"
    else:
        unit_type = "X"
    unit_nr = unit_string[-1]
    return unit_type, unit_nr


def extract_name_unit_id_from_unit_level_data_cleaning(
    filename: str,
) -> Tuple[str, str, str]:
    """Split a unit-level cleaning filename into components.

    Filenames are expected as ``"<name>_unit<id>_<annotator>.npy"``.

    Args:
        filename (str): Filename to parse.

    Returns:
        Tuple[str, str, str]: Tuple ``(name, unit_id, annotator)``.
    """

    name, unit_id, annotator = filename.split("_")
    unit_id = unit_id[4:]
    annotator = annotator[:-4]
    return name, unit_id, annotator


def match_label_to_patient_pts_time(
    default_label: np.ndarray, patient_pts: np.ndarray
) -> List[int]:
    """Align a default label indicator function to patient PTS frames.

    Args:
        default_label (np.ndarray): Indicator vector (per canonical frame) of shape ``(N,)``.
        patient_pts (np.ndarray): Watched frame times in seconds, rounded to 2 decimals.

    Returns:
        List[int]: Indicator value for each patient frame.
    """

    return [
        default_label[int(np.round(frame / 0.04, 0)) - 1]
        for _, frame in enumerate(patient_pts)
    ]


def get_list_of_patient_ids(patient_dict: Sequence[Dict[str, Any]]) -> List[int]:
    """Collect all patient IDs from an indexable sequence of dicts.

    Args:
        patient_dict (Sequence[Dict[str, Any]]): Sequence where each item has a `patient_id` key.

    Returns:
        List[int]: List of integer patient identifiers.
    """

    return [patient_dict[i]["patient_id"] for i in range(0, len(patient_dict))]
