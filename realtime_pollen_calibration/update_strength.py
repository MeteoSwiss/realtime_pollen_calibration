# Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS

# Distributed under the terms of the BSD 3-Clause License.

# SPDX-License-Identifier: BSD-3-Clause

"""A module for the update of the pollen emission strength."""

# Standard library
from datetime import datetime, timedelta

import numpy as np
import xarray as xr
from eccodes import (  # type: ignore
    codes_get,
    codes_get_array,
    codes_grib_new_from_file,
    codes_release,
)

# First-party
from realtime_pollen_calibration import utils


def read_pov_file(pov_infile, pol_fields, config_obj):
    """Read fields from pov_infile as defined in config.yaml.

    Args:
        pov_infile: GRIB2 file containing pollen fields.
        pol_fields: Names of the pollen fields.
        config_obj: Object containing the configuration set in config.yaml

    Returns:
        Fields needed for the pollen calibration and the new timestamp.

    """
    time_values = None
    cal_fields = {}
    with open(pov_infile, "rb") as fh:
        while True:
            # Get the next message
            rec = codes_grib_new_from_file(fh)
            if rec is None:
                break

            # Get the short name of the current field
            short_name = codes_get(rec, "shortName")

            # Extract field if present
            if short_name in pol_fields:
                cal_fields[short_name] = codes_get_array(rec, "values")

                data_date = str(codes_get(rec, "dataDate"))
                hour = str(codes_get(rec, "hour")).zfill(2)
                data_date_hour = data_date + hour

                date_obj = datetime.strptime(data_date_hour, "%Y%m%d%H") + timedelta(
                    hours=config_obj.hour_incr
                )
                date_obj_fmt = date_obj.strftime("%Y-%m-%dT%H:00:00.000000000")
                time_values = np.datetime64(date_obj_fmt)

            codes_release(rec)

    # Check if all mandatory fields for all species read are present. If not, exit.
    utils.check_mandatory_fields(cal_fields, pol_fields, pov_infile)

    return cal_fields, time_values


def update_strength_realtime(config_obj: utils.Config, verbose: bool = True):
    """Update the tune field.

    Args:
        config_obj: Configured data structure of class Config.
        verbose: Optional additional debug prints.

    Returns:
        File in GRIB2 format containing the updated temperature tune fields.

    """
    specs = ["ALNU", "BETU", "POAC", "CORY"]
    fields = ["tune", "saisn"]
    pol_fields = [x + y for x in specs for y in fields]
    cal_fields, time_values = read_pov_file(
        config_obj.pov_infile, pol_fields, config_obj
    )
    cal_fields_arrays = utils.create_data_arrays(
        cal_fields,
        utils.read_clon_clat(config_obj.const_file)[0],
        utils.read_clon_clat(config_obj.const_file)[1],
        time_values,
    )

    ds = xr.Dataset(cal_fields_arrays)
    ptype_present = utils.get_pollen_type(ds)

    if verbose:
        print(f"Detected pollen types in the DataSet provided: {ptype_present}")

    dict_fields = {}
    for pollen_type in ptype_present:
        obs_mod_data = utils.read_atab(
            pollen_type,
            config_obj.max_miss_stns,
            config_obj.station_obs_file,
            config_obj.station_mod_file,
            verbose=verbose,
        )
        change_tune = utils.get_change_tune(
            pollen_type,
            obs_mod_data,
            ds,
            config_obj,
            verbose=verbose,
        )
        tune_vec = utils.interpolate(
            change_tune,
            ds,
            pollen_type + "tune",
            config.obj,
            obs_mod_data.coord_stns,
            method="multiply",
        )
        dict_fields[pollen_type + "tune"] = tune_vec

    utils.to_grib(
        config_obj.pov_infile, config_obj.pov_outfile, dict_fields, config_obj.hour_incr
    )
