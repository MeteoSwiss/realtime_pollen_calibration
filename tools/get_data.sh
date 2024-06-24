#!/bin/bash

datapath=/store_new/mch/msopr/paa/RTcal_testdata/ 
localpath=$PWD

# copy Testdata for RT pollen calibration in to local directory
cp -r $datapath $localpath

echo <<EOF > $localpath/config.yaml
pov_infile : $localpath/RTcal_testdata/ART_POV_iconR19B08-grid_0001_BETU_POAC_2024042910
pov_outfile : $localpath/ART_POV_iconR19B08-grid_0001_tune
t2m_file : $localpath/RTcal_testdata/T_2M_KENDA-CH1_2024020118.gb2
const_file : $localpath/RTcal_testdata/CLON_CLAT_ICON-CH1.gb2
station_obs_file : $localpath/RTcal_testdata/pollen_measured_2024020118.atab
station_mod_file : $localpath/RTcal_testdata/pollen_modelled_2024020118.atab
hour_incr : 1
EOF

conda activate realtime-pollen-calibration
realtime-pollen-calibration update_phenology $localpath/config.yaml
realtime-pollen-calibration update_strength $localpath/config.yaml

