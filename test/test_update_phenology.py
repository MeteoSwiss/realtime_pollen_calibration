import pytest
from pathlib import Path
import eccodes

from realtime_pollen_calibration.update_phenology import update_phenology_realtime

def test_update_phenology_realtime(config, tmp_path):
    _, parsed_config = config
    
    # Run inside tmp_path so all outputs land there
    with pytest.MonkeyPatch().context() as mp:
        mp.chdir(tmp_path)
        update_phenology_realtime(parsed_config)

    expected_file = tmp_path / "ART_POV_iconR19B08-grid_0001_test_output"
    assert expected_file.exists(), f"Output file {expected_file} was not created"

    # Open GRIB2 file and check first field
    with open(expected_file, "rb") as f:
        gid = eccodes.codes_grib_new_from_file(f)
        assert gid is not None, "Could not read GRIB message"

        short_name = eccodes.codes_get(gid, "shortName")
        assert short_name == "BETUsaisn", "BETUsaisn is expected to be the first field but it is not!"
        
        eccodes.codes_release(gid)
