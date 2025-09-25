import shutil
import subprocess
import pytest
import yaml
import os
import tempfile
import urllib.request
import tarfile
from pathlib import Path

from realtime_pollen_calibration.set_up import set_up_config, Config

DATA_PATH = "/store_new/mch/msopr/osm/MISC/GIT_DATA/python/pollen_calibration"

def pytest_configure(config):
    # The below section is used for setting up local tests only.

    tmp_dir = pytest.TempPathFactory.from_config(config)

    definitions_dir = tmp_dir.mktemp('definitions')

    _set_grib_definitions_path(definitions_dir)

    data_dir = tmp_dir.mktemp('data')
    destination = _download_test_data(data_dir)

    config.data_dir = destination

@pytest.fixture(autouse=True)
def config(request, tmp_path) -> tuple[Path, Config]: 
    """Create config.yaml"""

    session_path = request.config.data_dir

    config = {
        "pov_infile": str(session_path / "ART_POV_iconR19B08-grid_0001_BETU_POAC_2024042910"),
        "pov_outfile": str(tmp_path / "ART_POV_iconR19B08-grid_0001_test_output"),
        "t2m_file": str(session_path / "T_2M_KENDA-CH1_2024020112.gb2"),
        "const_file": str(session_path / "CLON_CLAT_ICON-CH1.gb2"),
        "station_obs_file": str(session_path / "pollen_measured_2024020118.atab"),
        "station_mod_file": str(session_path / "pollen_modelled_2024020118.atab"),
        "hour_incr": 1,
        "max_miss_stns": 4
    }

    config_path = tmp_path / "config.yaml"

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    parsed_config = set_up_config(config_path)

    return config_path, parsed_config

def _download_test_data(test_directory: Path) -> Path:

    dest = test_directory / "RTcal_testdata"

    if 'balfrin' not in os.getenv('HOST', ''):
        # Copy data from remote using scp
        subprocess.run(["scp", "-r", f"balfrin:{DATA_PATH}", str(test_directory)], check=True)
        # Rename the copied directory
        source = test_directory / "pollen_calibration"
        shutil.move(str(source), str(dest))

    else:
        shutil.copytree(DATA_PATH, str(dest), dirs_exist_ok=True)
    return dest

@pytest.fixture(scope="session", autouse=True)
def test_data_dir(request) -> Path:
    return request.config.data_dir


def _set_grib_definitions_path(temp_dir) -> None:

    if 'GRIB_DEFINITION_PATH' not in os.environ:

        definitions = {'eccodes-cosmo-resources': "https://github.com/COSMO-ORG/eccodes-cosmo-resources/archive/refs/tags/v2.36.0.3.tar.gz",
                       'eccodes': "https://github.com/ecmwf/eccodes/archive/refs/tags/2.36.4.tar.gz"}

        definitions = _download_definitions(definitions, temp_dir)

        cosmo_definitions = next((p for p in definitions if 'eccodes-cosmo-resources' in p.name), None)
        print(f'COSMO ecCodes defintions: {cosmo_definitions}')

        definitions.remove(cosmo_definitions)
        eccodes_definitions = next((p for p in definitions if 'eccodes' in p.name), None)
        print(f'ecCodes defintions: {eccodes_definitions}')

        os.environ["GRIB_DEFINITION_PATH"] = f"{cosmo_definitions / 'definitions'}:{eccodes_definitions / 'definitions'}"

    print("GRIB_DEFINITION_PATH: %s" % os.getenv("GRIB_DEFINITION_PATH", 'unset'))

def _download_definitions(definitions: dict[str, str], definitions_dir: Path) -> list[Path]:

        print(f'Downloading definitions to: {definitions_dir}')
        for dir in definitions_dir.iterdir():
            if 'eccodes' in str(dir) and dir.is_dir():
                shutil.rmtree(dir)

        for name, url in definitions.items():

            _download_and_extract(
                url,
                definitions_dir)

        definitions: list[Path] = []

        for child in definitions_dir.iterdir():
            if child.is_dir() and 'eccodes' in str(child):

                definitions.append(child)

                # Keep only definitions folder from eccodes/eccodes-cosmo-resources
                for content in child.iterdir():
                    if content.is_dir() and content.name != 'definitions':
                        shutil.rmtree(content)
                    elif content.is_file():
                        content.unlink()

        return definitions


def _download_and_extract(url, extract_to: Path):

    print(f'Extracting {url} to {extract_to}')

    with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp_file:

        urllib.request.urlretrieve(url, tmp_file.name)

        with tarfile.open(tmp_file.name, "r:gz") as tar:
            tar.extractall(str(extract_to))
