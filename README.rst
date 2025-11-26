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

For decoding GRIB2 input data, ecCodes must be available as well as the ecCodes and COSMO ecCodes definitions. The location of the definitions must be stored in the environment variable ``ECCODES_DEFINITION_PATH``.
ecCodes definitions are installed with the ecCodes library, the COSMO ecCodes definitions are cloned and installed separately.
Be aware that the version of the COSMO eccodes definitions need to match the version of the ecCodes library.


Features
-------------------------------

The package includes two functionalities: one for updating the phenological fields and the other to update the strength of the pollen emission (tuning factor). Both can be executed independently.

The module ``update_phenology`` uses observed pollen concentrations to check whether the current ICON phenology matches the real world. In case of a mismatch the temperature sum thresholds are adapted to move forward or postpone the modelled pollen season. Technically speaking, the fields ``tthrs`` and ``tthre`` (for POAC, ``saisl`` instead) are adapted by using the GRIB2 fields  ``T_2M``, ``saisn`` and ``ctsum`` and the observed pollen concentrations of the last 120 hours at hourly resolution in ATAB format (missing data supported).

The module ``update_strength`` uses both observed and modelled pollen concentrations to check whether the current ICON concentrations match the real world. In case of a mismatch the tuning field is adapted accordingly. Technically speaking, the field ``tune`` is adapted by using the GRIB2 field ``saisn`` and the observed and modelled pollen concentrations of the last 120 hours at hourly resolution in ATAB format (missing data supported).

For further details of the realtime pollen calibration concept one may refer to the paper above.

How to configure the package
-------------------------------

The implementation includes a command line interface based on the click package. The configuration is done by editing the config.yaml file where the input/output is specified. The config.yaml should include the following entries (sample file names/values):

.. code-block:: console

 pov_infile : <path>/ART_POV_iconR19B08-grid_0001.gb2
 pov_outfile : <path>/ART_POV_iconR19B08-grid_0001_tune
 t2m_file : <path>/T_2M_KENDA-CH1_2024020112.gb2
 const_file : <path>/CLON_CLAT_ICON-CH1.gb2
 station_obs_file : <path>/pollen_measured_2024020118.atab
 station_mod_file : <path>/pollen_modelled_2024020118.atab
 hour_incr : 1
 max_miss_stns : 4
 weighting_type: switch
 max_param:
   ALNU: 3.389
   BETU: 4.046
   POAC: 1.875
   CORY: 7.738
 min_param:
   ALNU: 0.235
   BETU: 0.222
   POAC: 0.405
   CORY: 0.216
 ipstyle: rbf_mq
 eps_val: 1

``pov_infile``: This GRIB2 file must include the fields ``tthrs``, ``tthre`` (for POAC, ``saisl`` instead), ``saisn`` and ``ctsum`` if the module ``update_phenology`` is called. If the module ``update_strength`` is called ``pov_infile`` must include the fields ``saisn`` and ``tune``. If at least one of these mandatory fields is missing the package exits with status 1 and tells the user. ``pov_infile`` is used as template for ``pov_outfile``, i.e. the whole file is copied to ``pov_outfile`` with adapted values. Date and time information of ``pov_infile`` does not have to be correct, ICON just throws warnings.

``pov_outfile``: Same as ``pov_infile`` but with adapted values.

``t2m_file``: This GRIB2 file must include T_2M valid for 12h UTC of the current day (only used if the module ``update_phenology`` is called).

``const_file``: This GRIB2 file must contain CLON and CLAT of the unstructured grid used in ``pov_infile`` and ``t2m_file``.

``station_obs_file``: Observed hourly pollen concentrations (ATAB format) of the latest 120 hours relative to the target date of ``pov_outfile``. The timestamps of the data in this file may vary depending on data availability, time of extraction etc. Missing values are allowed but at least 50% of each station must be there. If not, the station is not used and set to missing. If more than ``max_miss_stns`` stations are missing, the package exits with status 1 and tells the user.

``station_mod_file``: Modelled hourly pollen concentrations (ATAB format) of the latest 120 hours relative to the target date of ``pov_outfile``. The timestamps of the data in this file may vary depending on data availability, time of extraction etc. In case of missing values the package exits with status 1 and tells the user. Same stations as in ``station_obs_file`` (only used if the module ``update_strength`` is called).

``hour_incr``: Increment of the timestamp of the outfile relative to the infile in hours (defaults to 1; negative values also supported). This parameter should be adapted if the calibration is done for a subsequent run more than one hour ahead.

``max_miss_stns``: Maximum number of stations allowed to be missing (defaults to 4). If more stations are missing, the package exits and tells the user.

``weighting_type``: Type of weighting used for the 120h pollen history. One of "constant" (default; same weights for all 120h), "switch" (sigmoidal decrease of older data), "linear" (linear decrease from 1 to zero back in time), "stepwise" (latest 36h get the same weights, older data zero).

``max_param``: Maximum allowed value for the tune parameter. If the updated value exceeds this maximum, it is set to this maximum.

``min_param``: Minimum allowed value for the tune parameter. If the updated value is below this minimum, it is set to this minimum.

``ipstyle``: Interpolation style used for spatial interpolation of station data to grid points. Options are "idw" (default; inverse distance weighting), "rbf_mq" (multiquadric radial basis function), "rbf_g" (gaussian radial basis function).

``eps_val``: Epsilon value used in the radial basis function interpolation. Relevant only if ``ipstyle`` is set to "rbf_mq" or "rbf_g". Defaults to 1.



Development Setup with Conda and Poetry
----------------------------------------

Building the Project
''''''''''''''''''''

Create a conda environment with the correct versions of Python (3.10) and Poetry (>=1.5):

.. code-block:: console

    cd realtime-pollen-calibration
    conda env create -n realtime-pollen-calibration --file conda_deps.yml
    conda activate realtime-pollen-calibration

Set the ecCodes definitions path (replace the value with paths to the correct versions):

.. code-block:: console

    conda env config vars set ECCODES_DEFINITION_PATH=<cosmo-definition-path:eccodes-definition-path>

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

Run the App
'''''''''''

.. code-block:: console

    poetry run realtime-pollen-calibration --help


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


The implementation assumes hourly resolution of the modelled and observed pollen concentrations (ATAB files). Hence, updating the tuning field  ``tune``) once per hour is recommended (i.e. running ``realtime-pollen-calibration update_strength <path_to_config>/config.yaml``).
Updating the phenological fields (i.e. ``tthrs`` and ``tthre`` (for POAC, ``saisl`` instead of ``tthre``)) should be done once per day (i.e. running ``realtime-pollen-calibration update_phenology <path_to_config>/config.yaml``).



Development Setup with Mchbuild
-------------------------------

Ensure you have mchbuild installed globally for your CSCS user. If not, ensure your pip is able to reach the MCH PyPI (Nexus) see https://meteoswiss.atlassian.net/wiki/x/XogHAQ, and then run the following:

.. code-block:: console

    cd ~
    module load python/3.10.8
    python -m venv mchbuild
    source mchbuild/bin/activate
    pip install mchbuild==0.8.0
    echo "append_path ~/mchbuild/bin" >> ~/.bashrc

.. code-block:: console

    cd realtime_pollen_calibration
    mchbuild conda.build
    mchbuild conda.test
    mchbuild conda.run

Try it out at and stop it with Ctrl-C. More information can be found in the `.mch-ci.yml <./.mch-ci.yml>`_ file and `<https://meteoswiss.atlassian.net/wiki/x/YoM-Jg>`_.


Generate Documentation
''''''''''''''''''''''

.. code-block:: console

    poetry run sphinx-build doc doc/_build

Then open the index.html file generated in *realtime-pollen-calibration/doc/_build/*.

