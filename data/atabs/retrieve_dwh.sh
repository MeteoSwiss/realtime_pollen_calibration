#!/bin/bash
# ALNU
#-----------------
# tthrs
~osm/bin/dwh_retrieve -s pollen_obs -t 202202030600-202202080500 --fmt atab --outfile=alnu_pollen_measured_values_2022020805.atab
# tune
~osm/bin/dwh_retrieve -s pollen_obs -t 202202170800-202202220700 --fmt atab --outfile=alnu_pollen_measured_values_2022022207.atab
# tthre (season end)
~osm/bin/dwh_retrieve -s pollen_obs -t 202203061500-202203111400 --fmt atab --outfile=alnu_pollen_measured_values_2022031114.atab

# BETU
#-----------------
# tthrs
~osm/bin/dwh_retrieve -s pollen_obs -t 202203131500-202203181400 --fmt atab --outfile=betu_pollen_measured_values_2022031814.atab
# tune
~osm/bin/dwh_retrieve -s pollen_obs -t 202203181000-202203230900 --fmt atab --outfile=betu_pollen_measured_values_2022032309.atab
# tthre (season end)
~osm/bin/dwh_retrieve -s pollen_obs -t 202205081500-202205131400 --fmt atab --outfile=betu_pollen_measured_values_2022051314.atab

# CORY
#-----------------
# tthrs (very small adjustment, we started the season late in the model)
~osm/bin/dwh_retrieve -s pollen_obs -t 202202051500-202202101400 --fmt atab --outfile=cory_pollen_measured_values_2022021014.atab
# tune
~osm/bin/dwh_retrieve -s pollen_obs -t 202202061100-202202111000 --fmt atab --outfile=cory_pollen_measured_values_2022021110.atab
# tthre (season end)
~osm/bin/dwh_retrieve -s pollen_obs -t 202203171500-202203221400 --fmt atab --outfile=cory_pollen_measured_values_2022032214.atab

# POAC
#-----------------
# tthrs
~osm/bin/dwh_retrieve -s pollen_obs -t 202204221500-202204271400 --fmt atab --outfile=poac_pollen_measured_values_2022042714.atab
# tune
~osm/bin/dwh_retrieve -s pollen_obs -t 202205080900-202205130800 --fmt atab --outfile=poac_pollen_measured_values_2022051308.atab
# saisl
~osm/bin/dwh_retrieve -s pollen_obs -t 202208051500-202208101400 --fmt atab --outfile=poac_pollen_measured_values_2022081014.atab
