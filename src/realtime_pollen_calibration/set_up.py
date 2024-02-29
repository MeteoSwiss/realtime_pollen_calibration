"""Setup the configuration."""

# Third-party
import yaml

# First-party
from realtime_pollen_calibration.utils import Config


def set_up_config(config_file: str):
    """Sets the configuration (path and time increment in hours)

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

    config.POV_infile = data["POV_infile"]

    config.const_file = data["const_file"]

    config.T2M_file= data["T2M_file"]

    config.POV_outfile = data["POV_outfile"]

    config.hour_incr = data["hour_incr"]
    
    return config
