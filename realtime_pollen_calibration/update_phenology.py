# Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS

# Distributed under the terms of the BSD 3-Clause License.

# SPDX-License-Identifier: BSD-3-Clause

"""A module for the update of start and end of the pollen season."""

# Standard library
import sys
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


def read_pov_file(pov_infile, pol_fields):
    """Read fields from pov_infile as defined in config.yaml.

    Args:
        pov_infile: GRIB2 file containing pollen fields.
        pol_fields: Names of the pollen fields.

    Returns:
        Fields for the pollen calibration.

    """
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

            # Delete the message
            codes_release(rec)

    # Check if all mandatory fields for all species read are present. If not, exit.
    utils.check_mandatory_fields(cal_fields, pol_fields, pov_infile)

    return cal_fields


def read_t2m_file(t2m_file, config_obj):
    time_values = None
    cal_fields = {}

    with open(t2m_file, "rb") as fh:
        while True:

            # Get the next message
            rec = codes_grib_new_from_file(fh)
            if rec is None:
                break
            short_name = codes_get(rec, "shortName")

            if short_name == "T_2M":
                cal_fields["T_2M"] = codes_get_array(rec, "values")

                # timestamp is needed. Take it from the T_2M field
                data_date = str(codes_get(rec, "dataDate"))
                hour = str(codes_get(rec, "hour")).zfill(2)
                data_date_hour = data_date + hour

                # Convert the string to a datetime object
                date_obj = datetime.strptime(data_date_hour, "%Y%m%d%H") + timedelta(
                    hours=config_obj.hour_incr
                )
                date_obj_fmt = date_obj.strftime("%Y-%m-%dT%H:00:00.000000000")
                time_values = np.datetime64(date_obj_fmt)
            codes_release(rec)
    if "T_2M" not in cal_fields:
        print(
            f"The mandatory field T_2M could not be read from {t2m_file}\n"
            "No update of the phenology is done until this is fixed!\n"
            "Pollen are still calculated but this should be fixed "
            "within a few days."
        )
        sys.exit(1)
    else:
        print("T_2M field has been read from t2m_file.")
    return cal_fields, time_values


def update_phenology_realtime(config_obj: utils.Config, verbose: bool = True):
    """Update the temperature threshold fields and POACsaisl.

    Args:
        config_obj: Configured data structure of class Config.
        verbose: Optional additional debug prints.

    Returns:
        File in GRIB2 format containing the updated temperature threshold fields
        and the length of the grass pollen season (POACsaisl).

    """
    pol_fields = ["ALNU", "BETU", "POAC", "CORY"]
    pol_fields = [
        x + y for x in pol_fields for y in ["tthrs", "tthre", "saisn", "ctsum"]
    ]
    pol_fields[9] = "POACsaisl"
    cal_fields = read_pov_file(config_obj.pov_infile, pol_fields)
    t2m_fields, time_values = read_t2m_file(config_obj.t2m_file, config_obj)
    cal_fields.update(t2m_fields)
    cal_fields_arrays = utils.create_data_arrays(
        cal_fields,
        utils.read_clon_clat(config_obj.const_file)[0],
        utils.read_clon_clat(config_obj.const_file)[1],
        time_values,
    )

    # Create an xarray Dataset with the DataArrays
    ds = xr.Dataset(cal_fields_arrays)

    if verbose:
        print(f"Detected pollen types in the DataSet: {utils.get_pollen_type(ds)}")

    dict_fields = {}
    for pollen_type in utils.get_pollen_type(ds):
        obs_mod_data = utils.read_atab(
            pollen_type,
            config_obj.max_miss_stns,
            config_obj.station_obs_file,
            verbose=verbose,
        )
        change_phenology_fields = utils.get_change_phenol(
            pollen_type, obs_mod_data, ds, verbose
        )

        for field_name, field_values in zip(
            change_phenology_fields._asdict(), change_phenology_fields
        ):
            if verbose:
                print(
                    f"Number of non-zero values in {field_name}: ",
                    np.count_nonzero(field_values),
                )
            if np.count_nonzero(field_values) > 0:
                dict_fields[pollen_type + field_name[7:]] = utils.interpolate(
                    field_values,
                    ds,
                    pollen_type + field_name[7:],
                    obs_mod_data.coord_stns,
                    method="sum",
                )

    utils.to_grib(
        config_obj.pov_infile, config_obj.pov_outfile, dict_fields, config_obj.hour_incr
    )
