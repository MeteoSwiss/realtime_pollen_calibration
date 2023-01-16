"""A module for the update of the pollen start and end of season in real time."""

# Third-party
import cfgrib  # type: ignore

# First-party
from realtime_pollen_calibration import utils


def update_phenology_realtime(file_data, file_grib, file_out, verbose=False):
    ds = cfgrib.open_dataset(file_grib, encode_cf=("time", "geography", "vertical"))
    pollen_type = utils.get_pollen_type(ds)
    array, _, coord_stns, missing_value, _ = utils.read_atab(pollen_type, file_data)
    array = utils.treat_missing(array, missing_value, verbose=verbose)
    change_tthrs, change_tthre = utils.get_change_phenol(
        pollen_type, array, ds, coord_stns, verbose
    )
    tthrs_vec = utils.interpolate(
        change_tthrs,
        ds,
        pollen_type + "tthrs",
        coord_stns,
        method="sum",
        verbose=verbose,
    )
    tthre_vec = utils.interpolate(
        change_tthre,
        ds,
        pollen_type + "tthre",
        coord_stns,
        method="sum",
        verbose=verbose,
    )
    dict_fields = {
        pollen_type + "tthrs": tthrs_vec,
        pollen_type + "tthre": tthre_vec,
    }
    utils.to_grib(file_grib, file_out, dict_fields)
