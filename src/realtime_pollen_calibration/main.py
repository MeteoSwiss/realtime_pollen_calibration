# Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS

# Distributed under the terms of the BSD 3-Clause License.

# SPDX-License-Identifier: BSD-3-Clause

"""Run test cases for realtime calibration."""

# Standard library
import os
from pathlib import Path

# First-party
from realtime_pollen_calibration import update_phenology_realtime
from realtime_pollen_calibration import update_strength_realtime

cwd = Path(os.getcwd())
data_path = str(cwd)

file_obs   = data_path + "/data/atabs/cory_alnu_pollen_measured_values_2024020118.atab"
file_POV   = data_path + "/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_all_specs_values"
file_T_2M  = data_path + "/data/grib2_files_ICON-CH1/iaf2024013000"
file_Const = data_path + "/data/grib2_files_ICON-CH1/lfff00000000c"
file_out   = data_path + "/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_2024020118_update_phen"
update_phenology_realtime.update_phenology_realtime(
    file_obs, file_POV, file_T_2M, file_Const, file_out, True
)

file_obs_stns = data_path + "/data/atabs/cory_alnu_pollen_measured_values_2024020118.atab"
file_mod_stns = data_path + "/data/atabs/cory_alnu_pollen_modelled_values_2024020118.atab"
file_POV   = data_path + "/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_2024020118_update_phen"
file_Const = data_path + "/data/grib2_files_ICON-CH1/lfff00000000c"
file_out   = data_path + "/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_2024020118_update_phen_tune"
update_strength_realtime.update_strength_realtime(
    file_obs_stns, file_mod_stns, file_POV, file_Const, file_out, True 
)
