"""A module for the update of the pollen strength in real time."""

# Third-party
import cfgrib  # type: ignore

# First-party
from realtime_pollen_calibration import utils


def update_strength_realtime(file_obs, file_mod, file_in, file_out, verbose):
    """Advance the tune field by one hour.

    Args:
        file_obs: Location of ATAB file containing the pollen concentration
                information at the stations.
        file_mod: Location of ATAB file for the modelled concentrations
        file_in: Location of GRIB file containing the following fields:
                'tune' and 'saisn'. Lat-lon information of the grid must be
                present in the file.
        file_out: Location of the desired output file.
        verbose: Optional additional debug prints.

    """
    ds = cfgrib.open_dataset(file_in, encode_cf=("time", "geography", "vertical"))
    pollen_type = utils.get_pollen_type(ds)
    array, array_mod, coord_stns, missing_value, istation_mod = utils.read_atab(
        pollen_type, file_obs, file_mod
    )
    array = utils.treat_missing(array, missing_value, verbose=verbose)
    change_tune = utils.get_change_tune(
        pollen_type,
        array,
        array_mod,
        ds,
        coord_stns,
        istation_mod,
        verbose=verbose,
    )
    # does not seem to have an important effect on the end result.
    # coord_stns2 = utils.set_stn_gridpoint(ds, coord_stns)
    tune_vec = utils.interpolate(
        change_tune,
        ds,
        pollen_type + "tune",
        coord_stns,
        method="multiply",
        verbose=verbose,
    )
    dict_fields = {pollen_type + "tune": tune_vec}
    utils.to_grib(file_in, file_out, dict_fields)
