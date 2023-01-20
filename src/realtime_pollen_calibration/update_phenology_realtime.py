"""A module for the update of the pollen start and end of season in real time."""

# Third-party
import cfgrib  # type: ignore
import numpy as np

# First-party
from realtime_pollen_calibration import utils


def update_phenology_realtime(file_obs, file_in, file_out, verbose=False):
    """Advance the temperature threshold fields by one hour.

    Args:
        file_obs: Location of ATAB file containing the pollen
                concentration information at the stations.
        file_in: Location of GRIB2 file containing the following fields:
                'T_2M', 'tthrs', 'tthre' (for POAC, 'saisl' instead),
                'saisn' and 'ctsum'. Lat-lon information of the grid must be
                present in the file.
        file_out: Location of the desired output file.
        verbose: Optional additional debug prints.

    """
    ds = cfgrib.open_dataset(file_in, encode_cf=("time", "geography", "vertical"))
    pollen_type = utils.get_pollen_type(ds)
    obs_mod_data = utils.read_atab(pollen_type, file_obs, verbose=verbose)
    change_phenology_fields = utils.get_change_phenol(
        pollen_type, obs_mod_data, ds, verbose
    )
    dict_fields = {}
    for field_name, field_values in zip(change_phenology_fields._asdict(), change_phenology_fields):
        if verbose:
            print(f"Number of non-zero values in {field_name}: ",
            np.count_nonzero(field_values),
            field_values)
        if np.count_nonzero(field_values) > 0:
            dict_fields[pollen_type + field_name[7:]] = utils.interpolate(
                field_values,
                ds,
                pollen_type + field_name[7:],
                obs_mod_data.coord_stns,
                method="sum",
                verbose=verbose,
            )
    utils.to_grib(file_in, file_out, dict_fields)
