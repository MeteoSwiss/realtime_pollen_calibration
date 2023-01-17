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


def read_atab(pollen_type, file_data, file_data_mod=""):
    def get_mod_stn_index(stn_indicators, stn_indicators_mod):
        [_, is1, is2] = np.intersect1d(
            stn_indicators, stn_indicators_mod, assume_unique=True, return_indices=True
        )
        return is2[np.argsort(is1)]

    def read_obs_header(file_data):
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
            coord_stns = list(zip(lat_stns, lon_stns))
        return coord_stns, missing_value, stn_indicators

    coord_stns, missing_value, stn_indicators = read_obs_header(file_data)
    data = pd.read_csv(
        file_data, header=17, delim_whitespace=True, parse_dates=[[1, 2, 3, 4, 5]]
    )
    data = data[data["PARAMETER"] == pollen_type].iloc[:, 2:].to_numpy()
    if file_data_mod != "":
        with open(file_data_mod, encoding="utf-8") as f:
            for line in f:
                if line.strip()[0:9] == "Indicator":
                    stn_indicators_mod = np.array(line.strip()[29:].split("         "))
                    break
        istation_mod = get_mod_stn_index(stn_indicators, stn_indicators_mod)
        data_mod = pd.read_csv(
            file_data_mod,
            header=18,
            delim_whitespace=True,
            parse_dates=[[3, 4, 5, 6, 7]],
        )
        data_mod = data_mod[data_mod["PARAMETER"] == pollen_type].iloc[:, 2:].to_numpy()
    else:
        data_mod = 0
        istation_mod = 0
    return data, data_mod, coord_stns, missing_value, istation_mod


def get_field_at(ds, field, coords):
    dist = (ds.latitude - coords[0]) ** 2 + (ds.longitude - coords[1]) ** 2
    return ds[field].where(dist == dist.min(), drop=True)


def interpolate(change, ds, field, coord_stns, method="multiply", verbose=False):
    nstns = len(coord_stns)
    pollen_type = field[:4]
    if method == "multiply":
        min_param = {"ALNU": 3.389, "BETU": 4.046, "POAC": 1.875, "CORY": 7.738}
        max_param = {"ALNU": 0.235, "BETU": 0.222, "POAC": 0.405, "CORY": 0.216}
    else:
        bigvalue = 1e10
        min_param = {
            "ALNU": bigvalue,
            "BETU": bigvalue,
            "POAC": bigvalue,
            "CORY": bigvalue,
        }
        max_param = {
            "ALNU": -bigvalue,
            "BETU": -bigvalue,
            "POAC": -bigvalue,
            "CORY": -bigvalue,
        }
    diff_lon = np.zeros((nstns,) + ds.longitude.shape)
    diff_lat = np.zeros((nstns,) + ds.longitude.shape)
    dist = np.zeros((nstns,) + ds.longitude.shape)
    change_vec = np.zeros_like(dist)
    eps = 0  # 1e-12
    for istation in range(nstns):
        diff_lon[istation, :] = (
            (ds.longitude - coord_stns[istation][1] + eps)
            * np.pi
            / 180
            * np.cos(ds.latitude * np.pi / 180)
        )
        diff_lat[istation, :] = (ds.latitude - coord_stns[istation][0]) * np.pi / 180
        dist[istation, :] = np.sqrt(
            diff_lon[istation, :] ** 2 + diff_lat[istation, :] ** 2
        )
        change_vec[istation, :] = change[istation]
    if method == "multiply":
        vec = np.maximum(
            np.minimum(
                ds[field].values
                * np.sum(change_vec / dist, axis=0)
                / np.sum(1 / dist, axis=0),
                min_param[pollen_type],
            ),
            max_param[pollen_type],
        )
        if verbose:
            i1 = 100
            i2 = 250
            print(f"dist from point ({i1},{i2}): {dist[:,i1,i2]}")
            print(
                f"Weighted change_tune by inverse distance: {np.sum(change_vec / dist, axis=0)[i1, i2]}"
            )
            print(f"Sum of inverse distance: {np.sum(1 / dist, axis=0)[i1, i2]}")
    elif method == "sum":
        vec = np.maximum(
            np.minimum(
                ds[field].values
                + np.sum(change_vec / dist, axis=0) / np.sum(1 / dist, axis=0),
                min_param[pollen_type],
            ),
            max_param[pollen_type],
        )
    return vec


def treat_missing(array, missing_value=-9999.0, tune_pol_default=1.0, verbose=False):
    array_missing = array == missing_value
    nstns = array.shape[1]
    skip_missing_stn = np.zeros(nstns)
    for istation in range(nstns):
        skip_missing_stn[istation] = np.count_nonzero(array_missing[:, istation])
        if verbose:
            print(
                f"Station n°{istation} has",
                f"{skip_missing_stn[istation]} missing values",
            )
        if skip_missing_stn[istation] > 0:
            if (
                np.count_nonzero(np.abs(array[:, istation] - missing_value) < 0.01)
                / len(array[:, istation])
                < 0.1
            ):
                idx1 = np.where(np.abs(array[:, istation] - missing_value) > 0.01)
                idx2 = np.where(np.abs(array[:, istation] - missing_value) < 0.01)
                if verbose:
                    print(
                        "Less than 10% of the data is missing, ",
                        f"mean of the rest is: {np.mean(array[idx1, istation])}",
                    )
                array[idx2, istation] = np.mean(array[idx1, istation])
            else:
                if verbose:
                    print("More than 10% of the data is missing")
                array[:, istation] = tune_pol_default
    return array


def get_change_tune(
    pollen_type,
    array,
    array_mod,
    ds,
    coord_stns,
    istation_mod,
    verbose=False,
):
    tune_pol_default = 1.0
    nstns = array.shape[1]
    change_tune = np.ones(nstns)
    for istation in range(nstns):
        # sum of hourly observed concentrations of the last 5 days
        sum_obs = np.sum(array[:, istation])
        # sum of hourly modelled concentrations of the last 5 days
        sum_mod = np.sum(array_mod[:, istation_mod[istation]])
        # tuning factor at the current station
        tune_stns = get_field_at(
            ds,
            pollen_type + "tune",
            coord_stns[istation],
        )
        # saison days at the current station
        # if > 0 then the pollen season has started
        saisn_stns = get_field_at(ds, pollen_type + "saisn", coord_stns[istation])
        if verbose:
            print(
                f"Current station n°{istation}, ",
                f"(lat: {coord_stns[istation][0]}, ",
                f"lon: {coord_stns[istation][1]}), ",
                f"last 120H concentration observed: {sum_obs}, ",
                f"modeled: {sum_mod}",
            )
            print(
                f"Current tune value {tune_stns.values[0][0]} ",
                f"and saisn: {saisn_stns.values[0][0]}",
            )
            print("-----------------------------------------")
        if (saisn_stns > 0) and ((sum_obs <= 720) or (sum_mod <= 720)):
            if verbose:
                print(
                    "Season started but low observation or modeled concentrations, "
                    "(tune)**(-1/24) = "
                    f"{(tune_pol_default / tune_stns.values[0][0]) ** (1 / 24)}"
                )
            change_tune[istation] = (tune_pol_default / tune_stns) ** (1 / 24)
        if (saisn_stns > 0) and (sum_obs > 720) and (sum_mod > 720):
            if verbose:
                print(
                    "Season started and high observation ", "and modeled concentrations"
                )
            change_tune[istation] = (sum_obs / sum_mod) ** (1 / 24)
        if verbose:
            print(f"Change tune is now: {change_tune[istation]}")
            print("-----------------------------------------")
    return change_tune


def get_change_phenol(pollen_type, array, ds, coord_stns, verbose=False):
    date = pd.Timestamp(ds.time.values).day_of_year + 1 + 31
    thr_con_24 = {"ALNU": 240, "BETU": 240, "POAC": 72, "CORY": 240}
    thr_con_120 = {"ALNU": 720, "BETU": 720, "POAC": 216, "CORY": 720}
    jul_days_excl = {"ALNU": 14, "BETU": 40, "POAC": 3, "CORY": 46}
    nstns = array.shape[1]
    change_tthrs = np.zeros(nstns)
    # change_tthre if not POAC, change_saisl if POAC
    change_tthre_saisl = np.zeros(nstns)
    for istation in range(nstns):
        tthrs_stns = get_field_at(ds, pollen_type + "tthrs", coord_stns[istation])
        if pollen_type != 'POAC':
            tthre_stns = get_field_at(ds, pollen_type + "tthre", coord_stns[istation])
        else:
            saisl_stns = get_field_at(ds, pollen_type + "saisl", coord_stns[istation])
        saisn_stns = get_field_at(ds, pollen_type + "saisn", coord_stns[istation])
        ctsum_stns = get_field_at(ds, pollen_type + "ctsum", coord_stns[istation])
        t_2m_stns = get_field_at(ds, "T_2M", coord_stns[istation]) - 273.15
        sum_obs_24 = np.sum(array[96:, istation])
        sum_obs = np.sum(array[:, istation])
        if verbose:
            print(
                f"Current station n°{istation}, ",
                f"(lat: {coord_stns[istation][0]}, ",
                f"lon: {coord_stns[istation][1]}), ",
                f"last 24H concentration observed: {sum_obs_24}, ",
                f"and last 120H {sum_obs}",
            )
            print(
                f"Cumulative temperature sum {ctsum_stns.values[0][0]} ",
                f"and threshold: {tthrs_stns.values[0][0]}",    
            )
            print(f"Temperature at station {t_2m_stns.values[0][0]}, " f"date: {date}")
            print("-----------------------------------------")
        # ADJUSTMENT OF SEASON START AND END AT THE BEGINNING OF THE SEASON
        if (sum_obs_24 >= thr_con_24[pollen_type]) and (sum_obs >= thr_con_120[pollen_type]) and ctsum_stns < tthrs_stns:
            change_tthrs[istation] = ctsum_stns - tthrs_stns
            if pollen_type != 'POAC':
                change_tthre_saisl[istation] = ctsum_stns - tthrs_stns
            if verbose:
                print("Big data and below threshold")
        elif (
            (0 <= sum_obs_24 < thr_con_24[pollen_type])
            and (0 <= sum_obs < thr_con_120[pollen_type])
            and (ctsum_stns > max(tthrs_stns, tthre_stns))
            and (0 < saisn_stns < 10)
        ):
            
            if pollen_type != 'POAC':
                change_tthre_saisl[istation] = t_2m_stns * (date - jul_days_excl[pollen_type])
                change_tthrs[istation] = t_2m_stns * (date - jul_days_excl[pollen_type])
            else: # case POAC
                if saisn_stns < saisl_stns:
                    change_tthrs[istation] = t_2m_stns * (date - jul_days_excl[pollen_type])
            if verbose:
                print("Low data and in first 10 days of season")
        # ADJUSTMENT OF SEASON END AT THE END OF THE SEASON
        if pollen_type != "POAC":
            if (
                (0 <= sum_obs_24 < thr_con_24[pollen_type])
                and (0 <= sum_obs < thr_con_120[pollen_type])
                and (tthre_stns - t_2m_stns * 5 * date < ctsum_stns < tthre_stns)
            ):
                if verbose:
                    print("Low data (end of season)")
                change_tthre_saisl[istation] += ctsum_stns - tthre_stns
            elif (
                (sum_obs_24 > thr_con_24[pollen_type])
                and (sum_obs > thr_con_120[pollen_type])
                and (tthre_stns > ctsum_stns > tthre_stns - t_2m_stns * 5 * date)
            ):
                if verbose:
                    print("Big data (end of season)")
                change_tthre_saisl[istation] += t_2m_stns * (date - jul_days_excl[pollen_type])
        else: # POAC
            if (
                (0 <= sum_obs_24 < thr_con_24[pollen_type])
                and (0 <= sum_obs < thr_con_120[pollen_type])
                and (saisn_stns < saisl_stns < saisn_stns + 5)
            ):
                if verbose:
                    print("Low data (end of season) POAC")
                change_tthre_saisl[istation] = saisn_stns - saisl_stns
            elif (
                (sum_obs_24 > thr_con_24[pollen_type])
                and (sum_obs > thr_con_120[pollen_type])
                and (saisn_stns < saisl_stns < saisn_stns + 5)
            ):
                if verbose:
                    print("Big data (end of season)")
                change_tthre_saisl[istation] = 1
        # FAILSAFE
        if change_tthrs[istation] > 0:
            change_tthrs[istation] = min(1000, change_tthrs[istation])
        elif change_tthrs[istation] <= 0:
            change_tthrs[istation] = max(-1000, change_tthrs[istation])
        if verbose:
            print(
                f"Change tthrs is now {change_tthrs[istation]} ",
                f"and change tthre is now {change_tthre_saisl[istation]}",
            )
            print("-----------------------------------------")
    return change_tthrs, change_tthre_saisl


def to_grib(inp, outp, dict_fields):
    # copy all the fields from input into output,
    # besides the ones in the dictionary given as input
    with open(inp, "rb") as fin, open(outp, "wb") as fout:
        while 1:
            gid = eccodes.codes_grib_new_from_file(fin)
            if gid is None:
                break
            # clone record
            clone_id = eccodes.codes_clone(gid)
            # get short_name

            short_name = eccodes.codes_get_string(clone_id, "shortName")
            # read values
            values = eccodes.codes_get_values(clone_id)
            eccodes.codes_set(
                clone_id, "dataTime", eccodes.codes_get(clone_id, "dataTime") + 100
            )
            if short_name in dict_fields:
                eccodes.codes_set_values(clone_id, dict_fields[short_name].flatten())
            else:
                eccodes.codes_set_values(clone_id, values)

            eccodes.codes_write(clone_id, fout)
            eccodes.codes_release(clone_id)
            eccodes.codes_release(gid)
        fin.close()
        fout.close()


def get_pollen_type(ds):
    pollen_types = ["ALNU", "BETU", "POAC", "CORY"]
    for var in ds:
        if var[:4] in pollen_types:
            return var[:4]
    return "Error: pollen type not recognized."


def set_stn_gridpoint(ds, coord_stns):
    nstns = len(coord_stns)
    lat_stns2 = np.zeros(nstns)
    lon_stns2 = np.zeros(nstns)
    for ist in range(nstns):
        lat_stns2[ist] = get_field_at(ds, "latitude", coord_stns[ist]).latitude.values[
            0
        ][0]
        lon_stns2[ist] = get_field_at(ds, "latitude", coord_stns[ist]).longitude.values[
            0
        ][0]
    coord_stns2 = list(zip(lat_stns2, lon_stns2))
    print(f"Changed the stations coordinates to: {coord_stns2}")
    return coord_stns2
