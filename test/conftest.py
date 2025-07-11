import shutil
import subprocess
import pytest
import yaml
import os
import tempfile
import urllib.request
import tarfile
from pathlib import Path

from realtime_pollen_calibration.set_up import set_up_config


def pytest_configure(config):
    # The below section is used for setting up local tests only.

    temp_dir = pytest.TempPathFactory.from_config(config).mktemp('definitions')

    _set_grib_definitions_path(temp_dir)

@pytest.fixture(scope="session")
def test_directory(tmp_path_factory: pytest.TempPathFactory) -> Path:

    return tmp_path_factory.mktemp("rtcal_test_env")


@pytest.fixture(scope="session")
def config(download_test_data: Path): 
    """Create config.yaml"""

    test_directory = download_test_data

    config = {
        "pov_infile": str(test_directory / "ART_POV_iconR19B08-grid_0001_BETU_POAC_2024042910"),
        "pov_outfile": str(test_directory / "ART_POV_iconR19B08-grid_0001_tune"),
        "t2m_file": str(test_directory / "T_2M_KENDA-CH1_2024020112.gb2"),
        "const_file": str(test_directory / "CLON_CLAT_ICON-CH1.gb2"),
        "station_obs_file": str(test_directory / "pollen_measured_2024020118.atab"),
        "station_mod_file": str(test_directory / "pollen_modelled_2024020118.atab"),
        "hour_incr": 1
    }

    config_path = test_directory / "config.yaml"

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    parsed_config = set_up_config(config_path)

    return config_path, parsed_config

@pytest.fixture(scope="session")
def download_test_data(test_directory: Path) -> Path:

    remote_path = "balfrin:/store_new/mch/msopr/osm/MISC/GIT_DATA/python/pollen_calibration"

    # Copy data from remote using scp
    subprocess.run(["scp", "-r", remote_path, str(test_directory)], check=True)

    # Rename the copied directory
    source = test_directory / "pollen_calibration"
    dest = test_directory / "RTcal_testdata"
    shutil.move(str(source), str(dest))

    return dest

def _set_grib_definitions_path(temp_dir):

    if 'GRIB_DEFINITION_PATH' not in os.environ:

        definitions = {'eccodes-cosmo-resources': "https://github.com/COSMO-ORG/eccodes-cosmo-resources/archive/refs/tags/v2.35.0.1dm1.tar.gz",
                       'eccodes': "https://github.com/ecmwf/eccodes/archive/refs/tags/2.35.0.tar.gz"}

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
