"""A module for the update of the pollen start and end of season in real time."""

# Third-party
import cfgrib  # type: ignore

# First-party
from realtime_pollen_calibration import utils


def update_strength_realtime(file_data, file_grib, file_out, verbose):
    data, _, lat_stns, lon_stns, missing_value, _ = utils.read_atab(file_data)

    pollen_types = ["ALNU", "BETU", "POAC", "CORY"]
    ipollen = 0
    array = data[data["PARAMETER"] == pollen_types[ipollen]].iloc[:, 2:].to_numpy()
    ds = cfgrib.open_dataset(file_grib, encode_cf=("time", "geography", "vertical"))
    array = utils.treat_missing(array, missing_value, verbose=verbose)
    change_tthrs, change_tthre = utils.get_change_phenol(
        array, ds, lat_stns, lon_stns, eps=1e-2
    )
    tthrs_vec = utils.interpolate(change_tthrs, ds, lat_stns, lon_stns, "sum")
    tthre_vec = utils.interpolate(change_tthre, ds, lat_stns, lon_stns, "sum")
    dict_fields = {
        pollen_types[ipollen] + "tthrs": tthrs_vec,
        pollen_types[ipollen] + "tthre": tthre_vec,
    }
    utils.to_grib(file_grib, file_out, dict_fields)
