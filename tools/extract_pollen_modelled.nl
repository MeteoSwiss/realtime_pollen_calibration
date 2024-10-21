&RunSpecification
 strict_nl_parsing  = .true.
 verbosity          = "moderate"
 diagnostic_length  = 110
 soft_memory_limit   = 29.0
 additional_diagnostic = .false.
 strict_usage = .true.
/

&GlobalResource
 dictionary           = "/oprusers/osm/opr/config/resources/dictionary_icon.txt",
 grib_definition_path = "/oprusers/osm/opr/config/resources/eccodes_definitions_cosmo",
                        "/oprusers/osm/opr/config/resources/eccodes_definitions_vendor"
 grib2_sample         = "/oprusers/osm/opr/config/resources/eccodes_samples/COSMO_GRIB2_default.tmpl"
 location_list        = "/oprusers/osm/opr/config/resources/location_list.txt"
 icon_grid_description= "/oprusers/osm/opr/data/grid_descriptions/icon_grid_0001_R19B08_mch.nc"
/

&GlobalSettings
 default_model_name = "icon"
 location_to_gridpoint="sn"
/

&ModelSpecification
 model_name         = "icon"
/

#-------------------------------------------------------------------------------------------------------------
# In core data
#-------------------------------------------------------------------------------------------------------------
# (1) Define base grid
#-------------------------------------------------------------------------------------------------------------
&Process
  in_file = "/scratch/mch/paa/wd/24013000_icon_CORY_ALNU_test_i1e_start_C-1E_calib/lm_coarse/iaf2024013000"
  out_type = "INCORE" /
&Process in_field = "HSURF", tag="HSURF" /
&Process in_field = "FR_LAND", tag="fr_land" /


#-------------------------------------------------------------------------------------------------------------
# Pollen assimilation
#-------------------------------------------------------------------------------------------------------------

&Process
  in_file="/scratch/mch/paa/wd/24013000_icon_CORY_ALNU_test_i1e_start_C-1E_calib/lm_coarse/lfff<DDHH>0000"
  out_file="pollen_modelled_2024020118.atab"
  out_type="XLS_TABLE", out_type_text1="ATAB", out_type_noundef=.false., out_type_epsminfo="no"
  locgroup="pollen_obs"
  tstart=0, tstop=66, tincr=1
/
&Process in_field = "DEN",     levlist=80 /
&Process in_field = "CORYsnc", levlist=80, tag="CORY", poper="product,DEN", new_field_id="CORY" /
&Process in_field = "ALNUsnc", levlist=80, tag="ALNU", poper="product,DEN", new_field_id="ALNU"  /

&Process out_field =  "CORY" /
&Process out_field =  "ALNU" /
