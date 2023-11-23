# Realtime Pollen Calibration

This repository calculates the pollen input fields needed for the real-time pollen calibration in ICON-ART. It is very similar to the FORTRAN implementation used in COSMO-ART.
More information about the Pollen module currently in the weather model COSMO can be found here:
<https://service.meteoswiss.ch/confluence/x/dYQYBQ>
And in this paper: (currently under review :)

This specific project also has a confluence page here:
<https://service.meteoswiss.ch/confluence/x/M_ahBw>

## Data Import

In the /data folder are case studies for four Species:

- Alder (ALNU)
- Birch (BETU)
- Hazel (CORY)
- Grasses (POAC)

The `identify_cases` folder contain text files that were used to identify timesteps with large changes in the tthrs, tthre, tune or saisl fields. Based on these files, two subsequent
hourly fields were selected to form case studies. For the first hour of the pair, additional atab files are provided. Based on these atab files and the input GRIB-fields the resulting fields one hour later can be calculated.

The `atabs` folder contains modelled and measured hourly averages of the past 120h (5 days).
Their use can be deducted from their names. The date at the end of the name corresponds to the
first hour of the case study pair.
Example name: `alnu_pollen_measured_values_2022020805`

The `grib2_files_cosmo1e` folder contains the GRIB2 files for each case study pair.
For each species there are 3 pairs

- one for the season start *tthrs/tthre*
- one for the tuning *tune*
- for the season end *tthre/saisl*

## Plotting

In the /notebook folder is a simple script that allows for plotting 2D-maps using xarray and iconarray.

## Start developing

Once you created or cloned this repository, make sure the installation is running properly. Install the package dependencies with the provided script `setup_env.sh`. This script also handles the installation of ecCodes cosmo definitions (for more on ecCode refer to the dedicated section below), sets the fieldextra path and checks the cartopy installation (currently deactivated).
Check available options with

```bash
tools/setup_env.sh -h
```

We distinguish development installations which are editable and have additional dependencies on formatters and linters from productive installations which are non-editable
and have no additional dependencies. Moreover we distinguish pinned installations based on exported (reproducible) environments and free installations where the installation
is based on top-level dependencies listed in `requirements/requirements.yml`. If you start developing, you might want to do an unpinned installation and export the environment:

```bash
tools/setup_env.sh -u -e -n <package_env_name>
```

*Hint*: If you are the package administrator, it is a good idea to understand what this script does, you can do everything manually with `conda` instructions.

*Hint*: Use the flag `-m` to speed up the installation using mamba. Of course you will have to install mamba first (we recommend to install mamba into your base
environment `conda install -c conda-forge mamba`. If you install mamba in another (maybe dedicated) environment, environments installed with mamba will be located
in `<miniconda_root_dir>/envs/mamba/envs`, which is not very practical.

The package itself is installed with `pip`:

```bash
conda activate <package_env_name>
pip install --editable .
```

*Warning:* Make sure you use the right pip, i.e. the one from the installed conda environment (`which pip` should point to something like `path/to/miniconda/envs/<package_env_name>/bin/pip`).

Once your package is installed, run the tests by typing:

```
conda activate <package_env_name>
pytest
```

If the tests pass, you are good to go. If not, contact the package administrator Simon Adamov. Make sure to update your requirement files and export your environments after installation
every time you add new imports while developing. Check the next section to find some guidance on the development process if you are new to Python and/or APN.

### ecCodes for GRIB decoding

Since this package uses cfgrib to decode GRIB data, ecCodes must be installed and the ecCodes and COSMO ecCodes definitions
made available. The location of the definitions is stored in the environment variable `GRIB_DEFINITION_PATH` in the conda environment.
 ecCodes definitions are installed with the ecCodes library by conda, the COSMO ecCodes definitions are cloned and installed
 separately. This is handled by `tools/setup_env.sh` and only needs to be done once, the settings are then stored in the conda
 environment! If you need a personalised version of ecCodes definitions, you can specify the path to your version
 in `GRIB_DEFINITION_PATH` (and `GRIB_SAMPLES_PATH` if needed) in `tools/setup_env.sh`.
 Be aware that the version of the COSMO eccodes definitions need to match the version of the ecCodes library.
 Please adapt both `requirements/requirements.yml` and `tools/setup_env.sh` if you need to change the ecCodes version.

### Roadmap to your first contribution

Generally, the source code of your library is located in `src/<library_name>`. The blueprint will generate some example code in `mutable_number.py`, `utils.py` and `cli.py`. `cli.py` thereby serves as an entry
point for functionalities you want to execute from the command line, it is based on the Click library. If you do not need interactions with the command line, you should remove `cli.py`. Moreover, of course there exist other options for command line interfaces,
a good overview may be found here (https://realpython.com/comparing-python-command-line-parsing-libraries-argparse-docopt-click/), we recommend however to use click. The provided example
code should provide some guidance on how the individual source code files interact within the library. In addition to the example code in `src/<library_name>`, there are examples for
unit tests in `tests/<library_name>/`, which can be triggered with `pytest` from the command line. Once you implemented a feature (and of course you also
implemented a meaningful test ;-)), you are likely willing to commit it. First, go to the root directory of your package and run pytest.

```bash
conda activate <package_env_name>
cd <package-root-dir>
pytest
```

Note that neither pytest, nor pre-commit, nor any of the linters invoked by the pre-commit hooks will be available in the production environment, so make sure you have a development environment
installed and activated. If you use the blueprint as is, pre-commit will not be triggered locally but only if you push to the main branch
(or push to a PR to the main branch). If you consider it useful, you can set up pre-commit to run locally before every commit by initializing it once. In the root directory of
your package, type:

```bash
pre-commit install
```

If you run `pre-commit` without installing it before (line above), it will fail and the only way to recover it, is to do a forced reinstallation (`conda install --force-reinstall pre-commit`).
You can also just run pre-commit selectively, whenever you want by typing (`pre-commit run --all-files`). Note that mypy and pylint take a bit of time, so it is really
up to you, if you want to use pre-commit locally or not. In any case, after running pytest, you can commit and the linters will run at the latest on the GitHub actions server,
when you push your changes to the main branch. Note that pytest is currently not invoked by pre-commit, so it will not run automatically. Automated testing should be implemented
in a Jenkins pipeline (template for a plan available in `jenkins/`. See the next section for more details.

## Development tools

As this package was created with the APN Python blueprint, it comes with a stack of development tools, which are described in more detail on
(<https://meteoswiss-apn.github.io/mch-python-blueprint/>). Here, we give a brief overview on what is implemented.

### Testing and coding standards

Testing your code and compliance with the most important Python standards is a requirement for Python software written in APN. To make the life of package
administrators easier, the most important checks are run automatically on GitHub actions. If your code goes into production, it must additionally be tested on CSCS
machines, which is only possible with a Jenkins pipeline (GitHub actions is running on a GitHub server).

### Pre-commit on GitHub actions

`.github/workflows/pre-commit.yml` contains a hook that will trigger the creation of your environment (unpinned) on the GitHub actions server and
then run pytest as well as various formatters and linters through pre-commit. This hook is only triggered upon pushes to the main branch (in general: don't do that)
and in pull requests to the main branch.

### Jenkins

Two jenkins plans are available in the `jenkins/` folder. On the one hand `jenkins/Jenkinsfile` controls the nightly (weekly, monthly, ...) builds, on the other hand
`jenkins/JenkinsJobPR` controls the pipeline invoked with the command `launch jenkins` in pull requests on GitHub. Your jenkins pipeline will not be set up
automatically. If you need to run your tests on CSCS machines, contact DevOps to help you with the setup of the pipelines. Otherwise, you can ignore the jenkinsfiles
and exclusively run your tests and checks on GitHub actions.

## Features

The project itself consists of two scripts: one for updating the season phenology for different pollen species and the other to update the strength of the pollen season based on observed and modelled concentrations.
- `update_phenology_realtime`:  Takes as input an ATAB file which contains the measured pollen concentrations, a GRIB file containing the following fields: `T_2M`, `tthrs`, `tthre` (for POAC, `saisl` instead), `saisn` and `ctsum` for a pollen species, and the name of the desired output file. The output file is in grib format, advanced by 1 hour and contains the fields `tthrs` and `tthre` (for POAC, `saisl` instead).
- `update_strength_realtime`: Takes as input two ATAB file which contain the measured and modeled pollen concentrations, a GRIB file containing the following fields: `tune` and `saisn` for a pollen species, and the name of the desired output file. The output file is in grib format, advanced by 1 hour and contains the field `tune`.
- `TODO`: Explain the expected ATAB format ?


## Credits

This package was created with [`copier`](https://github.com/copier-org/copier) and the [`MeteoSwiss-APN/mch-python-blueprint`](https://meteoswiss-apn.github.io/mch-python-blueprint/) project template.
