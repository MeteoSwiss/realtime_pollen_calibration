"""A module for the update of the pollen strength in real time."""

# Third-party
import cfgrib  # type: ignore

# First-party
from realtime_pollen_calibration import utils


def update_strength_realtime(file_data, file_data_mod, file_grib, file_out, verbose):
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
        pollen_types[ipollen],
        array,
        array_mod,
        ds,
        lat_stns,
        lon_stns,
        istation_mod,
        tune_pol_default=1.0,
    )
    tune_vec = utils.interpolate(
        change_tune,
        ds,
        pollen_types[ipollen] + "tune",
        lat_stns,
        lon_stns,
        "multiply",
        ipollen=ipollen,
    )
    dict_fields = {"ALNUtune": tune_vec}
    utils.to_grib(file_grib, file_out, dict_fields)
