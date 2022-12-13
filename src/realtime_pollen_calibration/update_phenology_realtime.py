"""A module for the update of the pollen start and end of season in real time."""

# Third-party
import cfgrib  # type: ignore

# First-party
from realtime_pollen_calibration import utils


def update_strength_realtime(file_data, file_data_mod, file_grib, verbose):
    data, data_mod, lat_stns, lon_stns, missing_value, istation_mod = utils.read_atab(
        file_data, file_data_mod
    )

    pollen_types = ["ALNU", "BETU", "POAC", "CORY"]
    ipollen = 0
    array = data[data["PARAMETER"] == pollen_types[ipollen]].iloc[:, 2:].to_numpy()
    array_mod = (
        data_mod[data_mod["PARAMETER"] == pollen_types[ipollen]].iloc[:, 2:].to_numpy()
    )
    ds = cfgrib.open_dataset(file_grib, encode_cf=("time", "geography", "vertical"))
    array = utils.treat_missing(array, missing_value, verbose=verbose)
    change_tune = utils.get_change_tune(
        array,
        array_mod,
        ds,
        lat_stns,
        lon_stns,
        istation_mod,
        tune_pol_default=1.0,
        eps=1e-2,
    )
    tune_vec = utils.interpolate(change_tune, ds, lat_stns, lon_stns, "COSMO")
    utils.to_grib(tune_vec)
