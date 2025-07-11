import pytest

from realtime_pollen_calibration.update_phenology import update_phenology_realtime

def test_update_phelology(caplog, config):

    _, parsed_config = config
    
    update_phenology_realtime(parsed_config)
