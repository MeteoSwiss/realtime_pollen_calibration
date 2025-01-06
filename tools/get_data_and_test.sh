#!/bin/bash

datapath=balfrin:/store_new/mch/msopr/osm/MISC/GIT_DATA/python/pollen_calibration
localpath=$PWD

# copy Testdata for RT pollen calibration in to local directory
scp -r $datapath $localpath
mv ./pollen_calibration ./RTcal_testdata

# temporarily: do a full test. Needs to be incorporated in the python
# test framework

# compile config.yaml
cat <<EOF > $localpath/config.yaml
pov_infile : $localpath/RTcal_testdata/ART_POV_iconR19B08-grid_0001_BETU_POAC_2024042910
pov_outfile : $localpath/ART_POV_iconR19B08-grid_0001_tune
t2m_file : $localpath/RTcal_testdata/T_2M_KENDA-CH1_2024020112.gb2
const_file : $localpath/RTcal_testdata/CLON_CLAT_ICON-CH1.gb2
station_obs_file : $localpath/RTcal_testdata/pollen_measured_2024020118.atab
station_mod_file : $localpath/RTcal_testdata/pollen_modelled_2024020118.atab
hour_incr : 1
EOF

# activate conda env
conda_root=$(conda info --base)
source $conda_root/etc/profile.d/conda.sh
conda init bash --no-user --install --system
conda activate RTcal

# run the test, capture exit status and log information

# Define the log file
LOG_FILE="update_phenology.log"

# Run update_phenology and save both stdout and stderr in the log file
realtime-pollen-calibration update_phenology $localpath/config.yaml > "$localpath/$LOG_FILE" 2>&1

# Check the exit status and tell the user
if [ $? -ne 0 ]; then
    echo "WARNING: Module update_phenology failed with exit status > 0. Check the log file for details: $localpath/$LOG_FILE"
else
    echo "Module update_phenology successful. Log information is available in: $localpath/$LOG_FILE"
fi

# Define the log file
LOG_FILE="update_strength.log"

# Run update_strength and save both stdout and stderr in the log file
realtime-pollen-calibration update_strength $localpath/config.yaml > "$localpath/$LOG_FILE" 2>&1

# Check the exit status and tell the user
if [ $? -ne 0 ]; then
    echo "WARNING: Module update_strength failed with exit status > 0. Check the log file for details: $localpath/$LOG_FILE"
else
    echo "Module update_strength successful. Log information is available in: $localpath/$LOG_FILE"
fi

# clean up
# remove output and config file
rm -f $localpath/ART_POV_iconR19B08-grid_0001_tune
rm -f $localpath/config.yaml
# remove test data
rm -rf $localpath/RTcal_testdata
