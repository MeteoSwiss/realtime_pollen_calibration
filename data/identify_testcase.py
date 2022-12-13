"""Loop through GRIB-files to identify test cases."""


# Standard library
import glob
import sys

# Third-party
import cfgrib  # type: ignore

variable = sys.argv[1]

path = "/store/s83/osm/KENDA-1/ANA22/det/"
files = list(set(glob.glob(path + "*")) - set(glob.glob(path + "*.*")))
files.sort()
files_red = files[120 * 24 + 1 :]

for file in files_red:
    data = cfgrib.open_dataset(
        file,
        encode_cf=("time", "geography", "vertical"),
        backend_kwargs={"filter_by_keys": {"shortName": variable}},
    )

    with open("./data/" + variable + ".txt", "a", encoding="UTF-8") as the_file:
        the_file.write(file + ": " + str(data[variable].values.mean()) + "\n")
