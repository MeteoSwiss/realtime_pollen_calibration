#!/usr/bin/env python3

from sys import argv, stdout, stderr, exit
import traceback
import datetime

from eccodes import *


# start day for temperature sum minus 1 - CAUTION: day 1 is 1 Dec
jul_days_excl = {"ALNUctsum" : 14, "BETUctsum" : 40, "POACctsum" : 46}

# pollen-specific base temperature for temperature sum (in deg. C)
t_base = {"ALNUctsum" : 5.2, "BETUctsum" : 9.0, "POACctsum" : 3.0}


T2MANA = 'T_2M_ana.grb2'
INPUT = 'INPUT.grb2'
OUTPUT = 'OUTPUT.grb2'

VERBOSE = 1  # verbose error reporting


def printf(format, *args):
    stdout.write(format % args)


def compute_ctsum(year, month, day):

    yyyymmdd = datetime.date(int(year), int(month), int(day))

    # day of year - count starts on 1 Dec
    if int(month) == 12:
       doy_dec1 = int(day)
    else:
       doy_dec1 = int(yyyymmdd.strftime("%j")) + 31

    printf("[compute_pollenctsum.py] Day of year (start counting on 1 Dec): %i\n", doy_dec1)

    # open file with analyzed T_2M
    ft2ma = open(T2MANA, 'rb')
    # read values
    t2ma_id = codes_grib_new_from_file(ft2ma)
    values_t2ma = codes_get_values(t2ma_id)
    # close file with analyzed T_2M
    ft2ma.close()

    # open input file with pollen specific cumulated temperature sums
    fin = open(INPUT, 'rb')
    # open output file for pollen specific cumulated temperature sums
    fout = open(OUTPUT, 'wb')

    while 1:
        gid = codes_grib_new_from_file(fin)
        if gid is None:
            break

        # clone record
        clone_id = codes_clone(gid)

        # get shortName
        shortName = codes_get_string(clone_id, 'shortName')

        # read values
        values_ctsum = codes_get_values(clone_id)

        # skip if doy_dec1 <= jul_days_excl
        if doy_dec1 > jul_days_excl[shortName]:
            printf("[compute_pollenctsum.py] ... do something: %s\n", shortName)

            # compute pollen specific cumulated temperature sum
            for i in range(len(values_ctsum)):
                # temperature in degrees Celsius
                value_degC = values_t2ma[i] - 273.15
                # add (with day of season weighted) value, if above pollen specific
                # temperatue threshold
                if value_degC >= t_base[shortName]:
                    values_ctsum[i] += value_degC * float(doy_dec1 - jul_days_excl[shortName])

        codes_set_key_vals(clone_id, 'dataDate=' + year + month + day)
        codes_set_values(clone_id, values_ctsum)

        codes_write(clone_id, fout)

        codes_release(clone_id)
        codes_release(gid)

    fin.close()
    fout.close()

    printf("\n")

    return 0


def main():
    try:
        if len(argv) == 4:
            compute_ctsum(argv[1], argv[2], argv[3])
        else:
            stderr.write("!!! ERROR: wrong number of command line arguments !!!\n")
            return 2
    except CodesInternalError as err:
        if VERBOSE:
            traceback.print_exc(file=sys.stderr)
        else:
            stderr.write(err.msg + '\n')

        return 1


if __name__ == "__main__":
    exit(main())
