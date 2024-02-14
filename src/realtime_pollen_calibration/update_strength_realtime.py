# Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS

# Distributed under the terms of the BSD 3-Clause License.

# SPDX-License-Identifier: BSD-3-Clause

"""A module for the update of the pollen strength in real time."""

# Third-party
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from eccodes import (
    codes_get,
    codes_get_array,
    codes_grib_new_from_file,
    codes_release,
)

# First-party
from realtime_pollen_calibration import utils


def update_strength_realtime(
    file_obs_stns, file_mod_stns, file_POV_tmp, file_Const, file_POV_out, hour_incr, verbose
):  # pylint: disable=R0801
    """Advance the tune field by one hour.

    Args:
        file_obs_stns: Location of ATAB file containing the pollen concentration
                information at the stations.
        file_mod_stns: Location of ATAB file for the modelled concentrations at the stations.
        file_POV_tmp: Location of GRIB file containing the following fields:
                'tune' and 'saisn'.
        file_Const: Location of GRIB2 file containing Longitudes and Latitudes of the 
                unstructured ICON grid.
        file_POV_out: Location of the desired output file.
        hour_incr: number of hour increments in the output compared to input.
        verbose: Optional additional debug prints.

    """
    
    fh_POV = open(file_POV_tmp, "rb")
    fh_Const = open(file_Const, "rb")
    
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
    fields= ["tune", "saisn"]
    pol_fields = [x + y for x in specs for y in fields]
    
    calFields = {}
    while True:
        # Get the next message
        recPOV = codes_grib_new_from_file(fh_POV)
        if recPOV is None:
            break
        
        # Get the short name of the current field
        short_name = codes_get(recPOV, "shortName")
        
        # Extract pollen fields if they are present
        for pol_field in pol_fields:
            if short_name == pol_field:
                calFields[pol_field] = codes_get_array(recPOV, "values")
            
                #timestamp is needed
                dataDate = str(codes_get(recPOV, "dataDate"))
                hour_old = str(str(codes_get(recPOV, "hour")).zfill(2))
                dataDateHour = dataDate + hour_old

                # Convert the string to a datetime object
                date_obj = datetime.strptime(dataDateHour, '%Y%m%d%H') + timedelta(hours=hour_incr)
                date_obj_fmt = date_obj.strftime('%Y-%m-%dT%H:00:00.000000000')
                time_values = np.datetime64(date_obj_fmt)
            
        # Delete the message
        codes_release(recPOV)
    
    # Close the GRIB files
    fh_POV.close()
    
    # Dictionary to hold DataArrays for each variable
    calFields_arrays = {}
    
    # Loop through variables to create DataArrays
    for var_name, data in calFields.items():
        data_array = xr.DataArray(data, coords={'index': np.arange(len(data))}, dims=['index'])
        data_array.coords['latitude'] = (('index'), CLAT)
        data_array.coords['longitude'] = (('index'), CLON)
        data_array.coords['time'] = time_values
        calFields_arrays[var_name] = data_array
        
    # Create an xarray Dataset with the DataArrays
    ds = xr.Dataset(calFields_arrays)

    ptype_present = utils.get_pollen_type(ds)
    if verbose:
        print(f"Detected pollen types in the DataSet provided: {ptype_present}")
    dict_fields = {}
    for pollen_type in ptype_present:
        obs_mod_data = utils.read_atab(pollen_type, file_obs_stns, file_mod_stns, verbose=verbose)
        change_tune = utils.get_change_tune(
            pollen_type,
            obs_mod_data,
            ds,
            verbose=verbose,
        )
        tune_vec = utils.interpolate(
            change_tune,
            ds,
            pollen_type + "tune",
            obs_mod_data.coord_stns,
            method="multiply",
        )
        dict_fields[pollen_type + "tune"] = tune_vec
    utils.to_grib(file_POV_tmp, file_POV_out, dict_fields, hour_incr)
