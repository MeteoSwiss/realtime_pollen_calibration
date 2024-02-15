# Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS

# Distributed under the terms of the BSD 3-Clause License.

# SPDX-License-Identifier: BSD-3-Clause

"""A module for the update of the pollen start and end of season in real time."""

# Standard library
from datetime import datetime, timedelta

# Third-party
import numpy as np
import xarray as xr
from eccodes import codes_get, codes_get_array, codes_grib_new_from_file, codes_release

# First-party
from realtime_pollen_calibration import utils


def update_phenology_realtime(
    file_paths: utils.FilePaths, hour_incr: int, verbose: bool = False
):
    """Advance the temperature threshold fields by one hour.

    Args:
        TODO: Fix docstring
        hour_incr: number of hour increments in the output compared to input.
        verbose: Optional additional debug prints.

    """

    fh_POV = open(file_paths.POV_in, "rb")
    fh_Const = open(file_paths.constants, "rb")
    fh_T_2M = open(file_paths.T_2M, "rb")

    # read CLON, CLAT
    while True:
        # Get the next message
        recConst = codes_grib_new_from_file(fh_Const)
        if recConst is None:
            break

        # Get the short name of the current field
        short_name = codes_get(recConst, "shortName")

        # Extract longitude and latitude of the ICON grid
        if short_name == "CLON":
            CLON = codes_get_array(recConst, "values")
        if short_name == "CLAT":
            CLAT = codes_get_array(recConst, "values")

        # Delete the message
        codes_release(recConst)

    # Close the GRIB file
    fh_Const.close()

    # read POV and extract available fields
    specs = ["ALNU", "BETU", "POAC", "CORY"]
    fields = ["tthrs", "tthre", "saisn", "ctsum"]
    pol_fields = [x + y for x in specs for y in fields]
    pol_fields[9] = "POACsaisl"

    calFields = {}
    while True:
        # Get the next message
        recPOV = codes_grib_new_from_file(fh_POV)
        if recPOV is None:
            break

        # Get the short name of the current field
        short_name = codes_get(recPOV, "shortName")

        # Extract and alter fields if they present
        for pol_field in pol_fields:
            if short_name == pol_field:
                calFields[pol_field] = codes_get_array(recPOV, "values")

        # Delete the message
        codes_release(recPOV)

    # Close the GRIB files
    fh_POV.close()

    # Read T_2M
    while True:
        # Get the next message
        recX = codes_grib_new_from_file(fh_T_2M)
        if recX is None:
            break

        # Get the short name of the current field
        short_name = codes_get(recX, "shortName")

        if short_name == "T_2M":
            calFields["T_2M"] = codes_get_array(recX, "values")

            # timestamp is needed. Take it from the T_2M field
            dataDate = str(codes_get(recX, "dataDate"))
            hour_old = str(str(codes_get(recX, "hour")).zfill(2))
            dataDateHour = dataDate + hour_old

            # Convert the string to a datetime object
            date_obj = datetime.strptime(dataDateHour, "%Y%m%d%H") + timedelta(
                hours=hour_incr
            )
            date_obj_fmt = date_obj.strftime("%Y-%m-%dT%H:00:00.000000000")
            time_values = np.datetime64(date_obj_fmt)

        codes_release(recX)

    # Close the GRIB files
    fh_T_2M.close()

    # Dictionary to hold DataArrays for each variable
    calFields_arrays = {}

    # Loop through variables to create DataArrays
    for var_name, data in calFields.items():
        data_array = xr.DataArray(
            data, coords={"index": np.arange(len(data))}, dims=["index"]
        )
        data_array.coords["latitude"] = (("index"), CLAT)
        data_array.coords["longitude"] = (("index"), CLON)
        data_array.coords["time"] = time_values
        calFields_arrays[var_name] = data_array

    # Create an xarray Dataset with the DataArrays
    ds = xr.Dataset(calFields_arrays)

    ptype_present = utils.get_pollen_type(ds)
    if verbose:
        print(f"Detected pollen types in the DataSet provided: {ptype_present}")
    dict_fields = {}
    for pollen_type in ptype_present:
        obs_mod_data = utils.read_atab(
            pollen_type, file_paths.obs_stations, verbose=verbose
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
    utils.to_grib(file_paths.POV_in, file_paths.POV_tmp, dict_fields, hour_incr)
