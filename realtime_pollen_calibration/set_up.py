"""Setup the configuration."""

import yaml

# First-party
from realtime_pollen_calibration.utils import Config


def set_up_config(config_file: str) -> Config:
    """Set the configuration (path and time increment in hours).

    Args:
        config_file (str): yaml configuration file

    Returns:
        Configured data structure of class Config.

    """
    with open(config_file, "r", encoding="utf-8") as fh_config_file:
        data = yaml.safe_load(fh_config_file)

    config = Config()

    config.station_obs_file = data["station_obs_file"]

    config.station_mod_file = data["station_mod_file"]

    config.pov_infile = data["pov_infile"]

    config.const_file = data["const_file"]

    config.t2m_file = data["t2m_file"]

    config.pov_outfile = data["pov_outfile"]

    config.max_miss_stns = data["max_miss_stns"]

    config.hour_incr = data["hour_incr"]

    return config
