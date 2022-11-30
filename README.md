# Realtime Pollen Calibration

This project translates the pollen calibration module from FORTRAN into Python.
More information about the Pollen module currently in the weather model COSMO can be found here:
https://service.meteoswiss.ch/confluence/x/dYQYBQ
And in this paper: (currently under review :)

This specific project also has a confluence page here:
https://service.meteoswiss.ch/confluence/x/M_ahBw
## Some instructions:
In the /data folder are two case studies for the Species *Alder* (i.e. ALNU).
- The first pair of laf files (i.e. GRIB2 files) are for the 2022-02-08 05h-06h should be used to calibrate the fields called **tthrs** and **tthre**.
- The second pair of laf files are for the 2022-02-22 07h-08h should be used to calibrate the field called **tune**.

- For the calibration of tthrs/tthre (i.e. phenology / season start and end) please use this file with the latest measurements: *pollen_measured_values_2022020805.atab*
- For the calibration of tune (i.e. tuning factor) please use this file with the latest measurements: *pollen_measured_values_2022022207.atab* and this file with the latest modelled values: *pollen_modelled_values_2022022207.atab*

In the /notebook folder is a simple script that allows for plotting 2D-maps using xarray and iconarray.

## Start developing

Once you created or cloned this repository, make sure the installation is running properly. Install the package dependencies with the provided script `setup_env.sh`.
Check available options with

```bash
setup_env.sh -h
```

We distinguish development installations which are editable and have additional dependencies on formatters and linters from productive installations which are non-editable
and have no additional dependencies. Moreover we distinguish pinned installations based on exported (reproducible) environments and free installations where the installation
is based on first level dependencies listed in `requirements/requirements.yml` and `requirements/dev-requirements.yml` respectively. If you start developing, you might want to do a free
development installation and export the environments right away.

```bash
setup_env.sh -d -e -m -n <package_env_name>
```

*Hint*: If you are the package administrator, it is a good idea to understand what this script does, you can do everything manually with `conda` instructions.

The package itself is installed with `pip`:

```bash
conda activate <package_env_name>
pip install --editable .
```

*Warning:* Make sure you use the right pip, i.e. the one from the installed conda environment (`which pip` should point to something like `path/to/miniconda/envs/<package_env_name>/bin/pip`).

Once your package is installed, run the tests by typing

```bash
pytest
```

If the tests pass, you are good to go. If not, contact the package administrator Simon Adamov. Make sure to update your requirement files and export your environments after installation
every time you add new imports while developing. Check the next section to find some guidance on the development process if you are new to Python and/ or APN.

To set the required Fieldextra, GRIB and ECCODES paths execute the following script:

```bash
./requirements/setup-conda-env.sh
```

## Development tools

As this package was created with the APN Python blueprint, it comes with a stack of development tools, which are described in more detail on
(<https://meteoswiss-apn.github.io/mch-python-blueprint/>). Here, we give a brief overview on what is implemented.

### Testing and coding standards

Testing your code and compliance with the most important Python standards is a requirement for Python software written in APN. To make the life of package
administrators easier, the most important checks are run automatically on GitHub actions. If your code goes into production, it must additionally be tested on CSCS
machines, which is only possible with a Jenkins pipeline (GitHub actions is running on a GitHub server).

### Pre-commit on GitHub actions

`.github/workflows/pre-commit.yml` contains a hook that will trigger the creation of your environment (unpinned, dev) on the GitHub actions server and
then run pytest as well as various formatters and linters through pre-commit. This hook is only triggered upon pushes to the main branch (in general: don't do that)
and in pull requests to the main branch.

### Jenkins

Two jenkins plans are available in the `jenkins/` folder. On the one hand `jenkins/Jenkinsfile` controls the nightly (weekly, monthly, ...) builds, on the other hand
`jenkins/JenkinsJobPR` controls the pipeline invoked with the command `launch jenkins` in pull requests on GitHub. Your jenkins pipeline will not be set up
automatically. If you need to run your tests on CSCS machines, contact DevOps to help you with the setup of the pipelines. Otherwise, you can ignore the jenkinsfiles
and exclusively run your tests and checks on GitHub actions.

## Features

- TODO

## Credits

This package was created with [`copier`](https://github.com/copier-org/copier) and the [`MeteoSwiss-APN/mch-python-blueprint`](https://meteoswiss-apn.github.io/mch-python-blueprint/) project template.
