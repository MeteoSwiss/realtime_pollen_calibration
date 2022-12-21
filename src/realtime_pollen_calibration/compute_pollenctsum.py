#!/usr/bin/env python3
"""Example for Updating Pollen Fields in GRIB Data."""
# pylint: disable-all
# Standard library
import datetime
import sys
import traceback

# Third-party
import eccodes  # type: ignore

# start day for temperature sum minus 1 - CAUTION: day 1 is 1 Dec
jul_days_excl = {"ALNUctsum": 14, "BETUctsum": 40, "POACctsum": 46}

# pollen-specific base temperature for temperature sum (in deg. C)
t_base = {"ALNUctsum": 5.2, "BETUctsum": 9.0, "POACctsum": 3.0}


T2MANA = "T_2M_ana.grb2"
INPUT = "INPUT.grb2"
OUTPUT = "OUTPUT.grb2"

VERBOSE = 1  # verbose error reporting


def printf(format_opt, *args):
    sys.stdout.write(format_opt % args)


def compute_ctsum(year, month, day):  # pylint: disable=R0914

    yyyymmdd = datetime.date(int(year), int(month), int(day))

    # day of year - count starts on 1 Dec
    if int(month) == 12:
        doy_dec1 = int(day)
    else:
        doy_dec1 = int(yyyymmdd.strftime("%j")) + 31

    printf(
        "[compute_pollenctsum.py] Day of year (start counting on 1 Dec): %i\n", doy_dec1
    )

    # open file with analyzed T_2M
    with open(T2MANA, "rb") as ft2ma:
        # read values
        t2ma_id = eccodes.codes_grib_new_from_file(ft2ma)
        values_t2ma = eccodes.codes_get_values(t2ma_id)
        # close file with analyzed T_2M
        ft2ma.close()

    # open input / output file with pollen specific cumulated temperature sums
    with open(INPUT, "rb") as fin, open(OUTPUT, "wb") as fout:
        while 1:
            gid = eccodes.codes_grib_new_from_file(fin)
            if gid is None:
                break

            # clone record
            clone_id = eccodes.codes_clone(gid)

            # get short_name
            short_name = eccodes.codes_get_string(clone_id, "short_name")

            # read values
            values_ctsum = eccodes.codes_get_values(clone_id)

            # skip if doy_dec1 <= jul_days_excl
            if doy_dec1 > jul_days_excl[short_name]:
                printf("[compute_pollenctsum.py] ... do something: %s\n", short_name)

                # compute pollen specific cumulated temperature sum
                for i in enumerate(values_ctsum):
                    # temperature in degrees Celsius
                    value_deg_c = values_t2ma[i] - 273.15
                    # add (with day of season weighted) value, if above pollen specific
                    # temperatue threshold
                    if value_deg_c >= t_base[short_name]:
                        values_ctsum[i] += value_deg_c * float(
                            doy_dec1 - jul_days_excl[short_name]
                        )

            eccodes.codes_set_key_vals(clone_id, "dataDate=" + year + month + day)
            eccodes.codes_set_values(clone_id, values_ctsum)

            eccodes.codes_write(clone_id, fout)

            eccodes.codes_release(clone_id)
            eccodes.codes_release(gid)

        fin.close()
        fout.close()

    printf("\n")

    return 0


def main():
    try:
        if len(sys.argv) == 4:
            compute_ctsum(sys.argv[1], sys.argv[2], sys.argv[3])
            return 0
        else:
            sys.stderr.write("!!! ERROR: wrong number of command line arguments !!!\n")
            return 2
    except eccodes.CodesInternalError as err:
        if VERBOSE:
            traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(err.msg + "\n")

        return 1


if __name__ == "__main__":
    sys.exit(main())
