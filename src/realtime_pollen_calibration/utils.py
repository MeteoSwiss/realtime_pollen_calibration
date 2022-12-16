"""Utils for the command line tool."""
# Standard library
import logging

# Third-party
import eccodes  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore


def count_to_log_level(count: int) -> int:
    """Map occurrence of the command line option verbose to the log level."""
    if count == 0:
        return logging.ERROR
    elif count == 1:
        return logging.WARNING
    elif count == 2:
        return logging.INFO
    else:
        return logging.DEBUG


def simple_idw(x, y, z, xi, yi):
    def distance_matrix(x0, y0, x1, y1):
        obs = np.vstack((x0, y0)).T
        interpo = np.vstack((x1, y1)).T

        # Make a distance matrix between pairwise observations
        # Note: from <http://stackoverflow.com/questions/1871536>
        # (Yay for ufuncs!)
        d0 = np.subtract.outer(obs[:, 0], interpo[:, 0])
        d1 = np.subtract.outer(obs[:, 1], interpo[:, 1])

        return np.hypot(d0, d1)

    dist = distance_matrix(x, y, xi, yi)

    # In IDW, weights are 1 / distance
    weights = 1.0 / dist

    # Make weights sum to one
    weights /= weights.sum(axis=0)

    # Multiply the weights for each interpolated point by all observed Z-values
    zi = np.dot(weights.T, z)
    return zi


def read_atab(file_data, file_data_mod=""):
    with open(file_data, encoding="utf-8") as f:
        for n, line in enumerate(f):
            if line.strip()[0:8] == "Latitude":
                lat_stns = np.fromstring(line.strip()[10:], sep=" ")
            if line.strip()[0:9] == "Longitude":
                lon_stns = np.fromstring(line.strip()[11:], sep=" ")
            if line.strip()[0:18] == "Missing_value_code":
                missing_value = float(line.strip()[20:])
            if line.strip()[0:9] == "Indicator":
                stn_indicators = np.array(line.strip()[11:].split("\t"))
            if n == 16:
                break
    data = pd.read_csv(
        file_data, header=17, delim_whitespace=True, parse_dates=[[1, 2, 3, 4, 5]]
    )
    if file_data_mod != "":
        with open(file_data_mod, encoding="utf-8") as f:
            for n, line in enumerate(f):
                if line.strip()[0:9] == "Indicator":
                    stn_indicators_mod = np.array(line.strip()[29:].split("         "))
                    break
        [_, is1, is2] = np.intersect1d(
            stn_indicators, stn_indicators_mod, assume_unique=True, return_indices=True
        )
        istation_mod = is2[np.argsort(is1)]

        data_mod = pd.read_csv(
            file_data_mod,
            header=18,
            delim_whitespace=True,
            parse_dates=[[3, 4, 5, 6, 7]],
        )
    else:
        data_mod = 0
        istation_mod = 0
    return data, data_mod, lat_stns, lon_stns, missing_value, istation_mod


def get_field_at(ds, field, lon, lat, eps=1e-2):
    return (
        ds[field]
        .where(
            (np.abs(ds.longitude - lon) < eps) & (np.abs(ds.latitude - lat) < eps),
            drop=True,
        )
        .values[0][0]
    )


def interpolate(change, ds, field, lat_stns, lon_stns, method="multiply"):
    nstns = len(lat_stns)
    if method == "multiply":
        min_param = [3.389, 4.046, 7.738, 1.875]
        max_param = [0.235, 0.222, 0.216, 0.405]
    else:
        min_param = 1e10 * np.ones(4)
        max_param = -1e10 * np.ones(4)
    ipollen = 0
    diff_lon = np.zeros((nstns,) + ds.longitude.shape)
    diff_lat = np.zeros((nstns,) + ds.longitude.shape)
    dist = np.zeros((nstns,) + ds.longitude.shape)
    for istation in range(nstns):
        diff_lon[istation, :] = (
            (ds.longitude - lon_stns[istation])
            * np.pi
            / 180
            * np.cos(ds.latitude * np.pi / 180)
        )
        diff_lat[istation, :] = (ds.latitude - lat_stns[istation]) * np.pi / 180
        dist[istation, :] = np.sqrt(
            diff_lon[istation, :] ** 2 + diff_lat[istation, :] ** 2
        )
    if method == "multiply":
        vec = np.maximum(
            np.minimum(
                ds[field].values
                * np.sum(change[:, np.newaxis, np.newaxis] / dist, axis=0)
                / np.sum(1 / dist, axis=0),
                min_param[ipollen],
            ),
            max_param[ipollen],
        )
    elif method == "sum":
        vec = np.maximum(
            np.minimum(
                ds[field].values
                + np.sum(change[:, np.newaxis, np.newaxis] / dist, axis=0)
                / np.sum(1 / dist, axis=0),
                min_param[ipollen],
            ),
            max_param[ipollen],
        )
    return vec


def treat_missing(array, missing_value=-9999.0, tune_pol_default=1.0, verbose=False):
    array_missing = array == missing_value
    skip_missing = np.count_nonzero(array_missing)
    nstns = array.shape[1]
    if skip_missing > 0:
        for istation in range(nstns):
            if (
                np.count_nonzero(np.abs(array[:, istation] - missing_value) < 0.01)
                / len(array[:, istation])
                < 0.1
            ):
                idx1 = np.where(np.abs(array[:, istation] - missing_value) > 0.01)
                idx2 = np.where(np.abs(array[:, istation] - missing_value) < 0.01)
                if verbose:
                    print(
                        f"Less than 10% of the data is missing, \
                    mean of the rest is: {np.mean(array[idx1, istation])}"
                    )
                array[idx2, istation] = np.mean(array[idx1, istation])
            else:
                if verbose:
                    print("More than 10% of the data is missing")
                array[:, istation] = tune_pol_default
    return array


def get_change_tune(
    array,
    array_mod,
    ds,
    lat_stns,
    lon_stns,
    istation_mod,
    tune_pol_default=1.0,
    eps=1e-2,
):
    nstns = array.shape[1]
    change_tune = np.zeros(nstns)
    for istation in range(nstns):
        # sum of hourly observed concentrations of the last 5 days
        sum_obs = np.sum(array[:, istation])
        # sum of hourly modelled concentrations of the last 5 days
        sum_mod = np.sum(array_mod[:, istation_mod])
        # tuning factor at the current station
        tune_stns = get_field_at(
            ds,
            "ALNU" + "tune",
            lon_stns[istation],
            lat_stns[istation],
            eps,
        )
        # saison days at the current station
        # if > 0 then the pollen season has started
        saisn_stns = get_field_at(
            ds,
            "ALNU" + "saisn",
            lon_stns[istation],
            lat_stns[istation],
            eps,
        )
        if (saisn_stns > 0) and ((sum_obs <= 720) or (sum_mod <= 720)):
            change_tune[istation] = (tune_pol_default / tune_stns) ** (1 / 24)
        if (saisn_stns > 0) and (sum_obs > 720) and (sum_mod > 720):
            change_tune[istation] = (sum_obs / sum_mod) ** (1 / 24)
    return change_tune


def get_change_phenol(array, ds, lat_stns, lon_stns, eps=1e-2):
    date = pd.Timestamp(ds.time.values).day_of_year + 1 + 31
    pollen_types = ["ALNU", "BETU", "POAC", "CORY"]
    ipollen = 0
    jul_days_excl = [14, 40, 3, 46]
    nstns = array.shape[1]
    change_tthrs = np.zeros(nstns)
    change_tthre = np.zeros(nstns)
    for istation in range(nstns):
        tthrs_stns = get_field_at(
            ds,
            pollen_types[ipollen] + "tthrs",
            lon_stns[istation],
            lat_stns[istation],
            eps,
        )
        tthre_stns = get_field_at(
            ds,
            pollen_types[ipollen] + "tthre",
            lon_stns[istation],
            lat_stns[istation],
            eps,
        )
        saisn_stns = get_field_at(
            ds,
            pollen_types[ipollen] + "saisn",
            lon_stns[istation],
            lat_stns[istation],
            eps,
        )
        ctsum_stns = get_field_at(
            ds,
            pollen_types[ipollen] + "ctsum",
            lon_stns[istation],
            lat_stns[istation],
            eps,
        )
        t_2m_stns = (
            get_field_at(ds, "T_2M", lon_stns[istation], lat_stns[istation], eps)
            - 273.15
        )
        sum_obs_24 = np.sum(array[96:, istation])
        sum_obs = np.sum(array[:, istation])
        # ADJUSTMENT OF SEASON START AND END AT THE BEGINNING OF THE SEASON
        if (sum_obs_24 >= 240) and (sum_obs >= 720) and ctsum_stns < tthrs_stns:
            change_tthrs[istation] = ctsum_stns - tthrs_stns
            change_tthre[istation] = ctsum_stns - tthrs_stns
        elif (
            (0 <= sum_obs_24 < 240)
            and (0 <= sum_obs < 720)
            and (ctsum_stns > max(tthrs_stns, tthre_stns))
            and (0 < saisn_stns < 10)
        ):
            change_tthrs[istation] = t_2m_stns * (date - jul_days_excl[0])
            change_tthre[istation] = t_2m_stns * (date - jul_days_excl[0])

        # ADJUSTMENT OF SEASON END AT THE END OF THE SEASON
        if (
            (0 <= sum_obs_24 < 240)
            and (0 <= sum_obs < 720)
            and (tthre_stns - t_2m_stns * 5 * date < ctsum_stns < tthre_stns)
        ):
            change_tthre[istation] += ctsum_stns - tthre_stns
        elif (
            (sum_obs_24 > 240)
            and (sum_obs > 720)
            and (tthre_stns > ctsum_stns > tthre_stns - t_2m_stns * 5 * date)
        ):
            change_tthre[istation] += t_2m_stns * (date - jul_days_excl[0])
        # FAILSAFE
        if change_tthrs[istation] > 0:
            change_tthrs[istation] = min(1000, change_tthrs[istation])
        elif change_tthrs[istation] <= 0:
            change_tthrs[istation] = max(-1000, change_tthrs[istation])
    return change_tthrs, change_tthre


def to_grib(input, output, dict_fields):
    # copy all the fields from input into output,
    # besides the ones in the dictionary given as input
    with open(input, "rb") as fin, open(output, "wb") as fout:
        while 1:
            gid = eccodes.codes_grib_new_from_file(fin)
            if gid is None:
                break
            # clone record
            clone_id = eccodes.codes_clone(gid)
            # get short_name

            short_name = eccodes.codes_get_string(
                clone_id, "shortName"
            )  # "short_name")
            # read values
            values = eccodes.codes_get_values(clone_id)
            # eccodes.codes_set_key_vals(clone_id, "dataDate=" + year + month + day)
            if short_name in dict_fields:
                eccodes.codes_set_values(clone_id, dict_fields[short_name].flatten())
            else:
                eccodes.codes_set_values(clone_id, values)
            eccodes.codes_write(clone_id, fout)
            eccodes.codes_release(clone_id)
            eccodes.codes_release(gid)
        fin.close()
        fout.close()
