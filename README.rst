===============
Realtime Pollen Calibration
===============


This repository contains the framework to update pollen input fields needed in ICON-ART (phenological and tuning input fields). It is very similar to the FORTRAN implementation used in COSMO-ART and is designed for the operational use at MeteoSwiss. Detailed information about the Pollen module and its operational setup can be found here:
`<https://meteoswiss.atlassian.net/wiki/spaces/APN/pages/1914937/Setup+pollen+in+ICON>`_.
The concept of the methodology is described in this paper: Adamov, S & Pauling, A (2023): A real-time calibration method for the numerical pollen forecast model COSMO-ART. Aerobiologia, 39, 327-344. It is available open access from `<https://link.springer.com/article/10.1007/s10453-023-09796-5>`_.

The package has been tested on Balfrin at CSCS only.

Test Case Data Import
-------------------------------

Test data for Hazel (CORY), Alder (ALNU), birch (BETU) and grass (POAC) pollen on the ICON-CH1 grid are used in the pytest tests. Please note that Ambrosia (AMBR) is not implemented.
The tools directory also includes the scripts that were used to generate the test data (fieldextra namelists and dwh_jretrieve commands). The intention is to document the data set provided and to facilitate the generation of a new test data set.


ecCodes for GRIB decoding
-------------------------------

For decoding GRIB2 input data, ecCodes must be installed and the ecCodes and COSMO ecCodes definitions made available. The location of the definitions is stored in the environment variable ``GRIB_DEFINITION_PATH``.
ecCodes definitions are installed with the ecCodes library, the COSMO ecCodes definitions are cloned and installed separately.
Be aware that the version of the COSMO eccodes definitions need to match the version of the ecCodes library.

 
## Features
-------------------------------

The package includes two functionalities: one for updating the phenological fields and the other to update the strength of the pollen emission (tuning factor). Both can be executed independently.

The module ``update_phenology`` uses observed pollen concentrations to check whether the current ICON phenology matches the real world. In case of a mismatch the temperature sum thresholds are adapted to move forward or postpone the modelled pollen season. Technically speaking, the fields ``tthrs`` and ``tthre`` (for POAC, ``saisl`` instead) are adapted by using the GRIB2 fields  ``T_2M``, ``saisn`` and ``ctsum`` and the observed pollen concentrations of the last 120 hours at hourly resolution in ATAB format (missing data supported).

The module ``update_strength`` uses both observed and modelled pollen concentrations to check whether the current ICON concentrations match the real world. In case of a mismatch the tuning field is adapted accordingly. Technically speaking, the field ``tune`` is adapted by using the GRIB2 field ``saisn`` and the observed and modelled pollen concentrations of the last 120 hours at hourly resolution in ATAB format (missing data supported).

Missing fields result in an error and thus no update of the fields. The input fields remain unchanged. If not all station data (observed or modelled) is available, the extraction will still take place and the update of the fields will be tried. However, input fields will remain unchanged if more than 10% of the data is missing.

For further details of the realtime pollen calibration concept one may refer to the paper above.

How to configure the package
-------------------------------

The implementation includes a command line interface based on the click package. The configuration is done by editing the config.yaml file where the input/output is specified. There is the option to configure the increment of the timestamp of the outfile relative to the infile in hours. The config.yaml should include the following entries (sample file names):

.. code-block:: console

 pov_infile : <path>/ART_POV_iconR19B08-grid_0001.gb2
 pov_outfile : <path>/ART_POV_iconR19B08-grid_0001_tune
 t2m_file : <path>/T_2M_KENDA-CH1_2024020112.gb2
 const_file : <path>/CLON_CLAT_ICON-CH1.gb2
 station_obs_file : <path>/pollen_measured_2024020118.atab
 station_mod_file : <path>/pollen_modelled_2024020118.atab
 hour_incr : 1

``pov_infile``: This GRIB2 file must include the fields ``tthrs``, ``tthre`` (for POAC, ``saisl`` instead), ``saisn`` and ``ctsum`` if the module ``update_phenology`` is called. If the module ``update_strength`` is called ``pov_infile`` must include the fields ``saisn`` and ``tune``. If at least one of these mandatory fields is missing the package exits with status 1 and tells the user. ``pov_infile`` is used as template for ``pov_outfile``, i.e. the whole file is copied to ``pov_outfile`` with adapted values. Date and time information of ``pov_infile`` does not have to be correct, ICON just throws warnings.

` pov_outfile``: Same as ``pov_infile`` but with adapted values.
``t2m_file``: This GRIB2 file must include T_2M valid for 12h UTC of the current day (only used if the module ``update_phenology`` is called).
``const_file``: This GRIB2 file must contain CLON and CLAT of the unstructured grid used in ``pov_infile`` and ``t2m_file``.
``station_obs_file``: Observed hourly pollen concentrations (ATAB format) of the latest 120 hours relative to the target date of ``pov_outfile``. The timestamps of the data in this file may vary depending on data availability, time of extraction etc. Missing values are allowed but at least 50% of each station must be there. If not, the package exits with status 1 and tells the user.
``station_mod_file``: Modelled hourly pollen concentrations (ATAB format) of the latest 120 hours relative to the target date of ``pov_outfile``. The timestamps of the data in this file may vary depending on data availability, time of extraction etc. In case of missing values the package exits with status 1 and tells the user. Same stations as in ``station_obs_file`` (only used if the module ``update_strength`` is called).
``hour_incr``: Increment of the timestamp of the outfile relative to the infile in hours (defaults to 1; negative values also supported). This parameter should be adapted if the calibration is done for a subsequent run more than one hour ahead.


How to run the package
-------------------------------

Review this section

The two modules are called this way:

.. code-block:: console

 conda activate <package_env_name>
 realtime-pollen-calibration update_phenology <path_to_config>/config.yaml
 realtime-pollen-calibration update_strength <path_to_config>/config.yaml

Help functionalities are also available:

.. code-block:: console

 realtime_pollen_calibration --help
 realtime_pollen_calibration update_phenology --help
 realtime_pollen_calibration update_strength --help


The implementation assumes hourly resolution of the modelled and observed pollen concentrations (ATAB files). Hence, updating the tuning field  `tune`) once per hour is recommended (i.e. running `realtime-pollen-calibration update_strength <path_to_config>/config.yaml`).
Updating the phenological fields (i.e. `tthrs` and `tthre` (for POAC, `saisl` instead of `tthre`)) should be done once per day (i.e. running `realtime-pollen-calibration update_phenology <path_to_config>/config.yaml`).


Development Setup with Mchbuild
-------------------------------

Ensure you have mchbuild installed globally for your CSCS user. If not run the following:

.. code-block:: console

    cd ~
    python -m venv mchbuild
    source mchbuild/bin/activate
    pip install mchbuild
    echo "append_path ~/mchbuild/bin" >> ~/.bashrc

.. code-block:: console

    cd realtime-pollen-calibration
    mchbuild conda.build
    mchbuild conda.test
    mchbuild conda.run

Try it out at and stop it with Ctrl-C. More information can be found in :file:`.mch-ci.yml` and https://meteoswiss.atlassian.net/wiki/x/YoM-Jg?atlOrigin=eyJpIjoiNDgxYmJjMDhmNDViNGIyNmI1OGU4NzY4NTFhNzViZWEiLCJwIjoiYyJ9.


Development Setup with Poetry
-----------------------------

Building the Project
''''''''''''''''''''

Create a conda environment with the correct Python version and Poetry:

.. code-block:: console

    cd realtime-pollen-calibration
    conda create -n realtime-pollen-calibration python=3.10 poetry
    conda activate realtime-pollen-calibration

Install the python dependencies with Poetry:

.. code-block:: console

    poetry install

Run Tests
'''''''''

.. code-block:: console

    poetry run pytest

Run Quality Tools
'''''''''''''''''

.. code-block:: console

    poetry run pylint realtime_pollen_calibration
    poetry run mypy realtime_pollen_calibration

Generate Documentation
''''''''''''''''''''''

.. code-block:: console

    poetry run sphinx-build doc doc/_build

Then open the index.html file generated in *realtime-pollen-calibration/doc/_build/*.

Run the App
'''''''''''

.. code-block:: console

    poetry run realtime-pollen-calibration --help
