import pytest

from realtime_pollen_calibration.update_strength import update_strength_realtime

def test_update_strength_realtime(caplog, config):

    _, parsed_config = config
    
    update_strength_realtime(parsed_config)
