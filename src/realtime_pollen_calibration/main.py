"""Run test cases for realtime calibration."""

# Standard library
import os

# First-party
from realtime_pollen_calibration import update_phenology_realtime
from realtime_pollen_calibration import update_strength_realtime

cwd = os.getcwd()

file_data = cwd + "/data/atabs/alnu_pollen_measured_values_2022021314.atab"
file_grib = cwd + "/data/grib2_files_cosmo1e/laf2022021314_ALNUtthrs_tthre"
file_out = cwd + "/data/2022020815_ALNUtthrs_tthre"
update_phenology_realtime.update_phenology_realtime(
    file_data, file_grib, file_out, False
)

file_data = cwd + "/data/atabs/alnu_pollen_measured_values_2022022207.atab"
file_data_mod = cwd + "/data/atabs/alnu_pollen_modelled_values_2022022207.atab"
file_grib = cwd + "/data/grib2_files_cosmo1e/laf2022022207_ALNUtune"
file_out = cwd + "/data/2022022208_ALNUtune"
update_strength_realtime.update_strength_realtime(
    file_data, file_data_mod, file_grib, file_out, False
)
