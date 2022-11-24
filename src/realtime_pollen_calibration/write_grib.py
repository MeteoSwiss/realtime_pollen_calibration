#!/usr/bin/env python3
"""Example File for Reading and Writing GRIB Data."""

# Third-party
from eccodes import codes_get_values  # type: ignore
from eccodes import codes_grib_new_from_file  # type: ignore
from eccodes import codes_set_values  # type: ignore
from eccodes import codes_write  # type: ignore

grib_input = "data/POACsaisl_c1e.gb1"

# ORIGINAL FIELD #
# open input file
with open(grib_input, "rb") as input_connection:
    # read values
    input_id = codes_grib_new_from_file(input_connection)
    input_values = codes_get_values(input_id)
    # close file
    input_connection.close()
    # display original values
    print(input_values.mean(), flush=True)

# UPDATE FIELD #
output_values = input_values * 2
# open output file (can be same as input)
with open(grib_input, "wb") as output_connection:
    # update the values in all cells
    codes_set_values(input_id, output_values)
    # write the updated field
    codes_write(input_id, output_connection)
    # close connection
    output_connection.close()

# DISPLAY UPDATED FIELD #
# open input file
with open(grib_input, "rb") as input_connection:
    # read values
    input_id = codes_grib_new_from_file(input_connection)
    input_values = codes_get_values(input_id)
    # close file
    input_connection.close()
    # display original values
    print(input_values.mean(), flush=True)
