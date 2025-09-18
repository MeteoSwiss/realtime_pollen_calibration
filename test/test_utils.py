"""Test module ``realtime_pollen_calibration/utils.py``."""

# Standard library
import logging

import cfgrib  # type: ignore
import numpy as np

# First-party
from realtime_pollen_calibration import utils

def test_count_to_log_level():
    assert utils.count_to_log_level(0) == logging.ERROR
    assert utils.count_to_log_level(1) == logging.WARNING
    assert utils.count_to_log_level(2) == logging.INFO
    assert utils.count_to_log_level(3) == logging.DEBUG


#    Set change_tune to be coherent with the next timestep output
#    in order to test the interpolation
#    note that for this computation there are some approximations, i.e.
#    AT one station 1/d_station >> 1/d_other_station and thus all the other
#    terms in the interpolation are neglected.
#    This test compares the implemented method for interpolation with the
#    results from the fortran implementation in COSMO with (=reference)


def test_interpolation(test_data_dir):
    # Specify the test case
    ds = cfgrib.open_dataset(
        str(test_data_dir) + "/laf2022022207_ALNUtune",
        encode_cf=("time", "geography", "vertical"),
    )
    ds2 = cfgrib.open_dataset(
        str(test_data_dir) + "/laf2022022208_ALNUtune",
        encode_cf=("time", "geography", "vertical"),
    )
    obs_mod_data = utils.read_atab(
        "ALNU",
        str(test_data_dir) + "/alnu_pollen_measured_values_2022022207.atab",
    )
    ######################
    # Specify the test
    nstns = len(obs_mod_data.coord_stns)
    tune_old = np.zeros(nstns)
    tune_next = np.zeros(nstns)
    for istation in range(nstns):
        tune_old[istation] = utils.get_field_at(
            ds, "ALNUtune", obs_mod_data.coord_stns[istation]
        )
        tune_next[istation] = utils.get_field_at(
            ds2, "ALNUtune", obs_mod_data.coord_stns[istation]
        )
    change_tune_2 = tune_next / tune_old
    tune_vec_2 = utils.interpolate(
        change_tune_2, ds, "ALNUtune", obs_mod_data.coord_stns, "multiply"
    )
    err = ds2.ALNUtune - tune_vec_2
    assert np.amax(np.abs(err.values)) < 1e-1
