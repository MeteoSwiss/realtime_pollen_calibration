#!/bin/bash
# ALNU
# tthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022020805 -s ALNUtthrs,ALNUtthre,ALNUctsum,ALNUsaisn,T_2M -o laf2022020805_ALNUtthrs_tthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022020806 -s ALNUtthrs,ALNUtthre,ALNUctsum,ALNUsaisn,T_2M -o laf2022020806_ALNUtthrs_tthre
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022022207 -s ALNUtune,ALNUctsum,ALNUsaisn,T_2M -o laf2022022207_ALNUtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022022208 -s ALNUtune,ALNUctsum,ALNUsaisn,T_2M -o laf2022022208_ALNUtune
# tthre (season end)
cd
# BETU
# tthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022031814 -s BETUtthrs,BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022031815_BETUtthrs_tthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022031815 -s BETUtthrs,BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022031814_BETUtthrs_tthre
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032309 -s BETUtune,BETUctsum,BETUsaisn,T_2M -o laf2022032309_BETUtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032310 -s BETUtune,BETUctsum,BETUsaisn,T_2M -o laf2022032310_BETUtune
# tthre (season end)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051314 -s BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022051314_BETUtthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051315 -s BETUtthre,BETUctsum,BETUsaisn,T_2M -o laf2022051315_BETUtthre

# CORY
# tthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021014 -s CORYtthrs,CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022021014_CORYtthrs_tthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021015 -s CORYtthrs,CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022021015_CORYtthrs_tthre
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021110 -s CORYtune,CORYctsum,CORYsaisn,T_2M -o laf2022021110_CORYtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022021111 -s CORYtune,CORYctsum,CORYsaisn,T_2M -o laf2022021111_CORYtune
# tthre (season end)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032214 -s CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022032214_CORYtthre
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022032215 -s CORYtthre,CORYctsum,CORYsaisn,T_2M -o laf2022032215_CORYtthre

# POAC
# tthrs (we started the season too late in the model no adjustments made)
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022042714 -s POACtthrs,POACtthre,POACctsum,POACsaisn,T_2M -o laf2022042714_POACtthrs
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022042715 -s POACtthrs,POACtthre,POACctsum,POACsaisn,T_2M -o laf2022042715_POACtthrs
# tune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051308 -s POACtune,POACctsum,POACsaisn,T_2M -o laf2022051308_POACtune
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022051309 -s POACtune,POACctsum,POACsaisn,T_2M -o laf2022051309_POACtune
# saisl
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022081014 -s POACsaisl,POACctsum,POACsaisn,T_2M -o laf2022081014_POACsaisl
fxfilter /store/s83/osm/KENDA-1/ANA22/det/laf2022081015 -s POACsaisl,POACctsum,POACsaisn,T_2M -o laf2022081015_POACsaisl
