#!/bin/bash
# ALNU
# tthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021314 --force -s ALNUtthrs,ALNUtthre,ALNUctsum,ALNUsaisn,T_2M -o laf2022021314_ALNUtthrs_tthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021315 --force -s ALNUtthrs,ALNUtthre,ALNUctsum,ALNUsaisn,T_2M -o laf2022021315_ALNUtthrs_tthre
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022022207 --force -s ALNUtune,ALNUctsum,ALNUsaisn,T_2M -o laf2022022207_ALNUtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022022208 --force -s ALNUtune,ALNUctsum,ALNUsaisn,T_2M -o laf2022022208_ALNUtune
# tthre (season end)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022031114 --force -s ALNUtthrs,ALNUtthre,ALNUctsum,ALNUsaisn,T_2M -o laf2022031114_ALNUtthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022031115 --force -s ALNUtthrs,ALNUtthre,ALNUctsum,ALNUsaisn,T_2M -o laf2022031115_ALNUtthre

# BETU
# tthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022031814 --force -s BETUtthrs,BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022031815_BETUtthrs_tthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022031815 --force -s BETUtthrs,BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022031814_BETUtthrs_tthre
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032309 --force -s BETUtune,BETUctsum,BETUsaisn,T_2M -o laf2022032309_BETUtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032310 --force -s BETUtune,BETUctsum,BETUsaisn,T_2M -o laf2022032310_BETUtune
# tthre (season end)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051314 --force -s BETUtthrs,BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022051314_BETUtthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051315 --force -s BETUtthrs,BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022051315_BETUtthre

# CORY
# tthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021014 --force -s CORYtthrs,CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022021014_CORYtthrs_tthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021015 --force -s CORYtthrs,CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022021015_CORYtthrs_tthre
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021110 --force -s CORYtune,CORYctsum,CORYsaisn,T_2M -o laf2022021110_CORYtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021111 --force -s CORYtune,CORYctsum,CORYsaisn,T_2M -o laf2022021111_CORYtune
# tthre (season end)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032214 --force -s CORYtthrs,CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022032214_CORYtthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032215 --force -s CORYtthrs,CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022032215_CORYtthre

# POAC
# tthrs (we started the season too late in the model no adjustments made)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022042714 --force -s POACtthrs,POACctsum,POACsaisn,T_2M -o laf2022042714_POACtthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022042715 --force -s POACtthrs,POACctsum,POACsaisn,T_2M -o laf2022042715_POACtthrs
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051308 --force -s POACtune,POACctsum,POACsaisn,T_2M -o laf2022051308_POACtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051309 --force -s POACtune,POACctsum,POACsaisn,T_2M -o laf2022051309_POACtune
# saisl
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022081014 --force -s POACtthrs,POACsaisl,POACctsum,POACsaisn,T_2M -o laf2022081014_POACsaisl
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022081015 --force -s POACtthrs,POACsaisl,POACctsum,POACsaisn,T_2M -o laf2022081015_POACsaisl
