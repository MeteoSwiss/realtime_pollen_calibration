"""Test module ``realtime_pollen_calibration/utils.py``."""
# Standard library
import logging

# Third-party
import cfgrib  # type: ignore
import numpy as np

# First-party
from realtime_pollen_calibration import utils


def test_count_to_log_level():
    assert utils.count_to_log_level(0) == logging.ERROR
    assert utils.count_to_log_level(1) == logging.WARNING
    assert utils.count_to_log_level(2) == logging.INFO
    assert utils.count_to_log_level(3) == logging.DEBUG


"""
    Set change_tune to be coherent with the next timestep output
    in order to test the interpolation
    note that for this computation there are some approximations, i.e.
    AT one station 1/d_station >> 1/d_other_station and thus all the other
    terms in the interpolation are neglected.
"""


def test_interpolation():
    # Specify the test case
    ds = cfgrib.open_dataset(
        "data/laf2022022207_filtered", encode_cf=("time", "geography", "vertical")
    )
    ds2 = cfgrib.open_dataset(
        "data/laf2022022208_filtered", encode_cf=("time", "geography", "vertical")
    )
    _, _, lat_stns, lon_stns, _, _ = utils.read_atab(
        "data/pollen_measured_values_2022020805.atab"
    )
    eps = 1e-2
    ######################
    # Specify the test
    nstns = len(lon_stns)
    tune_old = np.zeros(nstns)
    tune_next = np.zeros(nstns)
    for istation in range(nstns):
        tune_old[istation] = ds.ALNUtune.where(
            (np.abs(ds.longitude - lon_stns[istation]) < eps)
            & (np.abs(ds.latitude - lat_stns[istation]) < eps),
            drop=True,
        ).values[0][0]
        tune_next[istation] = ds2.ALNUtune.where(
            (np.abs(ds2.longitude - lon_stns[istation]) < eps)
            & (np.abs(ds2.latitude - lat_stns[istation]) < eps),
            drop=True,
        ).values[0][0]
    change_tune_2 = tune_next / tune_old
    tune_vec_2 = utils.interpolate(change_tune_2, ds, lat_stns, lon_stns, "COSMO")
    err = ds2.ALNUtune - tune_vec_2
    assert np.amax(np.abs(err.values)) < 1e-1
