#!/bin/bash -e

datapath=/users/paa/09_RTcalib/RTcal_testdata
localpath=$PWD

# copy Testdata for RT pollen calibration in to local directory
cp -r $datapath $localpath

# temporarily: do a full test. Needs to be incorporated in the python
# test framework

# compile config.yaml
cat <<EOF > $localpath/config.yaml
pov_infile : $localpath/RTcal_testdata/ART_POV_iconR19B08-grid_0001_BETU_POAC_2024042910
pov_outfile : $localpath/ART_POV_iconR19B08-grid_0001_tune
t2m_file : $localpath/RTcal_testdata/T_2M_KENDA-CH1_2024020118.gb2
const_file : $localpath/RTcal_testdata/CLON_CLAT_ICON-CH1.gb2
station_obs_file : $localpath/RTcal_testdata/pollen_measured_2024020118.atab
station_mod_file : $localpath/RTcal_testdata/pollen_modelled_2024020118.atab
hour_incr : 1
EOF

# activate conda env
source $CONDA_PREFIX/etc/profile.d/conda.sh
conda init bash --no-user --install --system
conda activate RTcal

# run the test
realtime-pollen-calibration update_phenology $localpath/config.yaml
realtime-pollen-calibration update_strength $localpath/config.yaml

# clean up
# remove output and config file
rm -f $localpath/ART_POV_iconR19B08-grid_0001_tune
rm -f $localpath/config.yaml
# remove test data
rm -rf $localpath/RTcal_testdata
