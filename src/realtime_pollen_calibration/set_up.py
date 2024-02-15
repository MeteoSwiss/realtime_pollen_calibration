"""TODO."""

# Standard library
from realtime_pollen_calibration.utils import FilePaths


def set_up_paths(data_path: str, date: str):
    """TODO

    Args:
        data_path (str): _description_
        date (str): _description_

    Returns:
        _type_: _description_

    """

    file_paths = FilePaths()
    file_paths.obs_stations = (
        data_path + f"/data/atabs/cory_alnu_pollen_measured_values_{date}.atab"
    )
    file_paths.mod_stations = (
        data_path + f"/data/atabs/cory_alnu_pollen_modelled_values_{date}.atab"
    )
    file_paths.POV_in = (
        data_path
        + f"/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_{date}_update_phen_tune4"
    )
    file_paths.T_2M = data_path + f"/data/grib2_files_ICON-CH1/iaf{date}"
    file_paths.constants = data_path + f"/data/grib2_files_ICON-CH1/lfff00000000c"
    file_paths.POV_tmp = (
        data_path
        + f"/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_{date}_update_phen_tune4_tmp"
    )
    file_paths.POV_out = (
        data_path
        + f"/data/grib2_files_ICON-CH1/ART_POV_iconR19B08-grid_0001_{date}_update_phen_tune5"
    )
    return file_paths
