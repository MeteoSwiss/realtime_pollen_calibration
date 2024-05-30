# Realtime Pollen Calibration

This repository contains the framework to update pollen input fields needed in ICON-ART (phenological and tuning input fields). It is very similar to the FORTRAN implementation used in COSMO-ART and is designed for the operational use at MeteoSwiss. Detailed information about the Pollen module and its operational setup can be found here:
<https://meteoswiss.atlassian.net/wiki/spaces/APN/pages/1914937/Setup+pollen+in+ICON>
The concept of the methodology is described in this paper: Adamov, S & Pauling, A (2023): A real-time calibration method for the numerical pollen forecast model COSMO-ART. Aerobiologia, 39, 327-344. It is available open access from https://link.springer.com/article/10.1007/s10453-023-09796-5

The package has been tested on Balfrin at CSCS only.

## Test Case Data Import

Test data for Hazel (CORY), Alder (ALNU), birch (BETU) and grass (POAC) pollen on the ICON-CH1 grid can be obtained by executing get_data.sh in the project root folder of the package. Please note that Ambrosia (AMBR) is not implemented.
The test data also includes the scripts that were used to generate the test data (fieldextra namelists and dwh_jretrieve commands). The intention is to document the data set provided and to facilitate the generation of a new test data set.


## Preparation

This project has been created from the
[MeteoSwiss Python blueprint](https://github.com/MeteoSwiss-APN/mch-python-blueprint)
for the CSCS infrastructure.
The recommended way to manage Python versions is with `Conda`
(https://docs.conda.io/en/latest/).
On CSCS machines it is recommended to install the leaner `Miniconda`
(https://docs.conda.io/en/latest/miniconda.html),
which offers enough functionality for most of our use cases.
If you don't want to do this step manually, you may use the script
`tools/setup_miniconda.sh`.
The default installation path of this script is the current working directory,
you might want to change that with the `-p` option to a common location for all
environments, like e.g. `$SCRATCH`. If you want the script to immediately
initialize conda (executing `conda init` and thereby adding a few commands at the
end of your `.bashrc`) after installation, add the `-u` option:

```bash
tools/setup_miniconda.sh -p $SCRATCH -u
```

In case you ever need to uninstall miniconda, do the following:

```bash
conda init --reverse --all
rm -rf $SCRATCH/miniconda
```

## Ho to install the package

Once you created or cloned this repository, make sure the installation is running properly. Install the package dependencies with the provided script `setup_env.sh`. This script also handles the installation of ecCodes cosmo definitions (for more on ecCode refer to the dedicated section below) and sets the fieldextra path.
Check available options with

```bash
tools/setup_env.sh -h
```
We distinguish pinned installations based on exported (reproducible) environments and free installations where the installation is based on top-level dependencies listed in `requirements/requirements.yml`. If you start developing, you might want to do an unpinned installation and export the environment:

```bash
tools/setup_env.sh -u -e -n <package_env_name>
```

*Hint*: If you are the package administrator, it is a good idea to understand what this script does, you can do everything manually with `conda` instructions.

The package itself is installed with `pip`. For development, install in editable mode:

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

If the tests pass, you are good to go. If not, contact the package administrators. Make sure to update your requirement files and export your environments after installation every time you add new imports while developing. Check the next section to find some guidance on the development process if you are new to Python and/or SEN.

### ecCodes for GRIB decoding

For decoding GRIB2 input data, ecCodes must be installed and the ecCodes and COSMO ecCodes definitions made available. The location of the definitions is stored in the environment variable `GRIB_DEFINITION_PATH` in the conda environment.
 ecCodes definitions are installed with the ecCodes library by conda, the COSMO ecCodes definitions are cloned and installed separately. This is handled by `tools/setup_env.sh` and only needs to be done once, the settings are then stored in the conda environment! If you want to use a personalised version of ecCodes definitions, you can specify the path to your version in `GRIB_DEFINITION_PATH` (and `GRIB_SAMPLES_PATH` if needed) in `tools/setup_env.sh`.
 Be aware that the version of the COSMO eccodes definitions need to match the version of the ecCodes library.
 Please adapt both `requirements/requirements.yml` and `tools/setup_env.sh` if you need to change the ecCodes version.


## Features

The package includes two functionalities: one for updating the phenological fields and the other to update the strength of the pollen emission (tuning factor). Both can be executed independently.

The module `update_phenology` uses observed pollen concentrations to check whether the current ICON phenology matches the real world. In case of a mismatch the temperature sum thresholds are adapted to move forward or postpone the modelled pollen season. Technically speaking, the fields `tthrs` and `tthre` (for POAC, `saisl` instead) are adapted by using the GRIB2 fields  `T_2M`, `saisn` and `ctsum` and the observed pollen concentrations of the last 120 hours at hourly resolution in ATAB format (missing data supported).

The module `update_strength` uses both observed and modelled pollen concentrations to check whether the current ICON concentrations match the real world. In case of a mismatch the tuning field is adapted accordingly. Technically speaking, the field `tune` is adapted by using the GRIB2 field `saisn` and the observed and modelled pollen concentrations of the last 120 hours at hourly resolution in ATAB format (missing data supported).

Missing fields result in an error and thus no update of the fields. The input fields remain unchanged. If not all station data (observed or modelled) is available, the extraction will still take place and the update of the fields will be tried. However, input fields will remain unchanged if more than 10% of the data is missing.

For further details of the realtime pollen calibration concept one may refer to the paper above.




### How to configure the package

The implementation includes a command line interface based on the click package. The configuration is done by editing the config.yaml file where the input/output is specified. There is the option to configure the increment of the timestamp of the outfile relative to the infile in hours. The config.yaml should include the following entries (see also the config.yaml provided):

```bash
POV_infile : <path>/ART_POV_iconR19B08-grid_0001.gb2
POV_outfile : <path>/ART_POV_iconR19B08-grid_0001_tune
T2M_file : <path>/T_2M_KENDA-CH1_2024020118.gb2
const_file : <path>/CLON_CLAT_ICON-CH1.gb2
station_obs_file : <path>/pollen_measured_2024020118.atab
station_mod_file : <path>/pollen_modelled_2024020118.atab
hour_incr : 1
```
`POV_infile`: This GRIB2 file must include the fields `tthrs`, `tthre` (for POAC, `saisl` instead), `saisn` and `ctsum` if the module `update_phenology` is called. If the module `update_strength` is called `POV_infile` must include the fields `saisn` and `tune`. `POV_infile` is used as template for `POV_outfile`, i.e. the whole file is copied to `POV_outfile` with adapted values. Date and time information of `POV_infile` does not have to be correct, ICON just throws warnings.
`POV_outfile`: Same as `POV_infile` but with adapted values.
`T2M_file`: This GRIB2 file must include T_2M (only used if the module `update_phenology` is called).
`const_file`: This GRIB2 file must contain CLON and CLAT of the unstructured grid used in `POV_infile` and `T_2M`.
`station_obs_file`: Observed hourly pollen concentrations (ATAB format) of the latest 120 hours relative to the target date of `POV_outfile`. The timestamps of the data in this file may vary depending on data availability, time of extraction etc. Missing values are allowed.
`station_mod_file`: Modelled hourly pollen concentrations (ATAB format) of the latest 120 hours relative to the target date of `POV_outfile`. The timestamps of the data in this file may vary depending on data availability, time of extraction etc. Missing values are allowed. Same stations as in `station_obs_file` (only used if the module `update_strength` is called).
`hour_incr`: Increment of the timestamp of the outfile relative to the infile in hours (defaults to 1; negative values also supported). This parameter should be adapted if the calibration is done for a subsequent run more than one hour ahead.


### How to run the package

The two modules are called this way:
```bash
conda activate <package_env_name>
realtime-pollen-calibration update_phenology <path_to_config>/config.yaml
realtime-pollen-calibration update_strength <path_to_config>/config.yaml
```
Help functionalities are also available:

```bash
realtime_pollen_calibration --help
realtime_pollen_calibration update_phenology --help
realtime_pollen_calibration update_strength --help
```

The implementation assumes hourly resolution of the modelled and observed pollen concentrations (ATAB files). Hence, updating the tuning field once per hour is recommended. The phenology model of ICON is called once per day at 12 UTC model time. Hence, we recommend to update the phenological fields (i.e. `tthrs` and `tthre` (for POAC, `saisl` instead of `tthre`)) also once per day some time before 12 UTC (model time) so that the updated fields can be used by ICON.


### Unit test

Generally, the source code of your library is located in `src/<library_name>`. In addition, there is a unit test for the interpolation routine in `tests/<library_name>/`, which can be triggered with `pytest` from the command line. Once you implemented a new feature including a meaningful test, you are likely willing to commit it. Before committing go to the root directory of your package and run pytest.

```bash
conda activate <package_env_name>
cd <package-root-dir>
pytest
```

If you use the tools provided by the blueprint as is, pre-commit will not be triggered locally but only if you push to the main branch
(or push to a PR to the main branch). If you consider it useful, you can set up pre-commit to run locally before every commit by initializing it once. In the root directory of
your package, type:

```bash
pre-commit install
```

If you run `pre-commit` without installing it before (line above), it will fail and the only way to recover it, is to do a forced reinstallation (`conda install --force-reinstall pre-commit`).
You can also just run pre-commit selectively, whenever you want by typing (`pre-commit run --all-files`). We recommend to commit after pytest and pre-commit are successful. After pushing to the main branch (or into a branch with a PR to the main branch), the linters will run on the GitHub actions server. Note that pytest is currently not invoked by pre-commit, so it will not run automatically. Automated testing can be set up with GitHub Actions or be implemented in a Jenkins pipeline (template for a plan available in `jenkins/`. See the next section for more details.

## Development tools

As this package was created with the SEN Python blueprint, it comes with a stack of development tools, which are described in more detail on
(<https://meteoswiss-apn.github.io/mch-python-blueprint/>). Here, we give a brief overview on what is implemented.

### Testing and coding standards

Testing your code and compliance with the most important Python standards is a requirement for Python software written in SEN. To make the life of package
administrators easier, the most important checks are run automatically on GitHub actions.

### Pre-commit on GitHub actions

`.github/workflows/pre-commit.yml` contains a hook that will trigger the creation of your environment (unpinned) on the GitHub actions server and
then run various formatters and linters through pre-commit. This hook is only triggered upon pushes to the main branch (in general: don't do that)
and in pull requests to the main branch.

### Jenkins

A jenkinsfile is available in the `jenkins/` folder. It can be used for a multibranch jenkins project, which builds
both commits on branches and PRs. Your jenkins pipeline will not be set up
automatically. If you need to run your tests on CSCS machines, contact DevOps to help you with the setup of the pipelines. Otherwise, you can ignore the jenkinsfiles
and exclusively run your tests and checks on GitHub actions.



## Credits

This package was created with [`copier`](https://github.com/copier-org/copier) and the [`MeteoSwiss-APN/mch-python-blueprint`](https://meteoswiss-apn.github.io/mch-python-blueprint/) project template.
