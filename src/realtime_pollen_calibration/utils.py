"""Utils for the command line tool."""
# Standard library
import logging
from collections import namedtuple

# Third-party
import eccodes  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore

obs_mod_data = namedtuple(
    "obs_mod_data",
    ["data_obs", "coord_stns", "missing_value", "data_mod", "istation_mod"],
    defaults=[None, None],
)
change_phenology_fields = namedtuple(
    "change_phenology_fields", ["change_tthrs", "change_tthre", "change_saisl"]
)


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


def read_atab(
    pollen_type: str, file_obs: str, file_mod: str = "", verbose: bool = False
) -> obs_mod_data:
    """Read the pollen concentrations and the station locations from ATAB files.

    Args:
        pollen_type: String describing the pollen type analysed.

        file_obs: Location of the observation ATAB file.
        file_mod: Location of the model ATAB file. (Optional)
        verbose: Optional additional debug prints.

    Returns:
        data: Array containing the observed concentration values.
        data_mod: Array containing the modelled concentration values.
                (if provided).
        coord_stns: List of (lat, lon) tuples of the stations' coordinates.
        missing_value: Value considered as a missing measurement.
        istation_mod: Index for the correspondence between the columns of data
                and the columns of data_mod (if file_data_mod is provided.)

    """

    def get_mod_stn_index(stn_indicators, stn_indicators_mod):
        """Find the correspondence between station indices in the two files."""
        [_, is1, is2] = np.intersect1d(
            stn_indicators, stn_indicators_mod, assume_unique=True, return_indices=True
        )
        return is2[np.argsort(is1)]

    def read_obs_header(file_data: str):
        """Read the info from the header of the ATAB.

        Args:
            file_data: Location of the ATAB file.

        Returns:
            coord_stns: List of (lat, lon) tuples of the stations' coordinates.
            missing_value: Value considered as a missing measurement.
            stn_indicators: Used for correspondence between
                    observed and modelled data.

        """
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

    coord_stns, missing_value, stn_indicators = read_obs_header(file_obs)
    data = pd.read_csv(
        file_obs, header=17, delim_whitespace=True, parse_dates=[[1, 2, 3, 4, 5]]
    )
    data = data[data["PARAMETER"] == pollen_type].iloc[:, 2:].to_numpy()
    if file_mod != "":
        with open(file_mod, encoding="utf-8") as f:
            for line in f:
                if line.strip()[0:9] == "Indicator":
                    stn_indicators_mod = np.array(line.strip()[29:].split("         "))
                    break
        istation_mod = get_mod_stn_index(stn_indicators, stn_indicators_mod)
        data_mod = pd.read_csv(
            file_mod,
            header=18,
            delim_whitespace=True,
            parse_dates=[[3, 4, 5, 6, 7]],
        )
        data_mod = data_mod[data_mod["PARAMETER"] == pollen_type].iloc[:, 4:].to_numpy()
    else:
        data_mod = 0
        istation_mod = 0
    data = treat_missing(data, missing_value, verbose=verbose)
    return obs_mod_data(data, coord_stns, missing_value, data_mod, istation_mod)


def treat_missing(array, missing_value=-9999.0, tune_pol_default=1.0, verbose=False):
    """Treat the missing values of the input array.

    Args:
        array: Array containing the concentration values.
        missing_value: Value considered as a missing measurement.
        tune_pol_default: Default value to which all values of a station
                are set if more than 10% of the observations are missing.
        verbose: Optional additional debug prints.

    Returns:
        array: Modified array with removed missing values.

    """
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


def get_field_at(ds, field: str, coords: tuple):
    """Get the field in a xarray.DataSet at a given location.

    Args:
        ds: xarray.DataSet.
        field: Name of the field.
        coords: (lat, lon) tuple of the location.

    Returns:
        Field at the desired location.

    """
    dist = (ds.latitude - coords[0]) ** 2 + (ds.longitude - coords[1]) ** 2
    return ds[field].where(dist == dist.min(), drop=True)


def interpolate(  # pylint: disable=R0913,R0914
    change,
    ds,
    field: str,
    coord_stns,
    method: str = "multiply",
    verbose: bool = False,
):
    """Interpolate the change of a field from its values at the stations.

    Args:
        change: Value of the change at the stations.
        ds: xarray.DataSet.
        field: Name of the field to be interpolated on.
        coord_stns: List of (lat, lon) tuples of the stations' coordinates.
        method: Either 'multiply' (strength) or add (phenology)
        verbose: Optional additional debug prints.

    Returns:
        vec: Obtained field over the full grid.
    This is a reproduction of the IDW implemented in COSMO by Simon Sadamov,
    with different threshold (minima and maxima) for different species.

    """
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
    eps = 1e-14  # prevents division by zero
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
                "Weighted change_tune by inverse distance: "
                f"{np.sum(change_vec / dist, axis=0)[i1, i2]}"
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


def get_change_tune(  # pylint: disable=R0913
    pollen_type,
    obs_mod_data,
    ds,
    verbose=False,
):
    """Compute the change of the tune field.

    Args:
        pollen_type: String describing the pollen type analysed.
        obs_mod_data: NamedTuple which must contain the last 120H
            pollen concentration observed and modelled and the
            coordinates of the stations.
        ds: xarray.DataSet containing 'tune' and 'saisn'.
        verbose: Optional additional debug prints.

    Returns:
        change_tune: Amount by which tune should be changed at each station
    The new tune value corresponds to:
    tune(station, T+dT) = tune(station, T) * change_tune(station).

    """
    tune_pol_default = 1.0
    nstns = obs_mod_data.data_obs.shape[1]
    change_tune = np.ones(nstns)
    for istation in range(nstns):
        # sum of hourly observed concentrations of the last 5 days
        sum_obs = np.sum(obs_mod_data.data_obs[:, istation])
        # sum of hourly modelled concentrations of the last 5 days
        sum_mod = np.sum(obs_mod_data.data_mod[:, obs_mod_data.istation_mod[istation]])
        # tuning factor at the current station
        tune_stns = get_field_at(
            ds,
            pollen_type + "tune",
            obs_mod_data.coord_stns[istation],
        )
        # saison days at the current station
        # if > 0 then the pollen season has started
        saisn_stns = get_field_at(
            ds, pollen_type + "saisn", obs_mod_data.coord_stns[istation]
        )
        if verbose:
            print(
                f"Current station n°{istation}, ",
                f"(lat: {obs_mod_data.coord_stns[istation][0]}, ",
                f"lon: {obs_mod_data.coord_stns[istation][1]}), ",
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


def get_change_phenol(
    pollen_type, obs_mod_data, ds, verbose=False
):  # pylint: disable=R0912,R0914,R0915
    """Compute the change of the temperature thresholds for the phenology.

    Args:
        pollen_type: String describing the pollen type analysed.
        obs_mod_data: NamedTuple which must contain the last 120H
            pollen concentration observed and the
            coordinates of the stations.
        ds: xarray.DataSet containing 'T_2M', 'tthrs', 'tthre'
            (for POAC, 'saisl' instead), 'saisn' and 'ctsum'.
        verbose: Optional additional debug prints.

    Returns:
        change_tthrs: Amount by which tthrs should be changed at each station
        change_tthre_saisl: As above for tthre or saisl for POAC.
    The new threshold value corresponds to:
    tthrs(station, T+dT) = tthrs(station, T) + change_tthrs(station).

    """
    date = pd.Timestamp(ds.time.values).day_of_year + 1 + 31
    thr_con_24 = {"ALNU": 240, "BETU": 240, "POAC": 72, "CORY": 240}
    thr_con_120 = {"ALNU": 720, "BETU": 720, "POAC": 216, "CORY": 720}
    failsafe = {"ALNU": 1000, "BETU": 2500, "POAC": 6000, "CORY": 2500}
    jul_days_excl = {"ALNU": 14, "BETU": 40, "POAC": 3, "CORY": 46}
    nstns = obs_mod_data.data_obs.shape[1]
    change_tthrs = np.zeros(nstns)
    change_tthre = np.zeros(nstns)
    change_saisl = np.zeros(nstns)
    for istation in range(nstns):
        tthrs_stns = get_field_at(
            ds, pollen_type + "tthrs", obs_mod_data.coord_stns[istation]
        )
        if pollen_type != "POAC":
            tthre_stns = get_field_at(
                ds, pollen_type + "tthre", obs_mod_data.coord_stns[istation]
            )
        else:
            saisl_stns = get_field_at(
                ds, pollen_type + "saisl", obs_mod_data.coord_stns[istation]
            )
        saisn_stns = get_field_at(
            ds, pollen_type + "saisn", obs_mod_data.coord_stns[istation]
        )
        ctsum_stns = get_field_at(
            ds, pollen_type + "ctsum", obs_mod_data.coord_stns[istation]
        )
        t_2m_stns = get_field_at(ds, "T_2M", obs_mod_data.coord_stns[istation]) - 273.15
        sum_obs_24 = np.sum(obs_mod_data.data_obs[96:, istation])
        sum_obs = np.sum(obs_mod_data.data_obs[:, istation])
        if verbose:
            print(
                f"Current station n°{istation}, ",
                f"(lat: {obs_mod_data.coord_stns[istation][0]}, ",
                f"lon: {obs_mod_data.coord_stns[istation][1]}), ",
                f"last 24H concentration observed: {sum_obs_24}, ",
                f"and last 120H {sum_obs}",
            )
            print(
                f"Cumulative temperature sum {ctsum_stns.values[0][0]} ",
                f"and threshold (start): {tthrs_stns.values[0][0]}",
                f" and end: {tthre_stns.values[0][0]}",
                f" and saisn: {saisn_stns.values[0][0]}",
            )
            print(f"Temperature at station {t_2m_stns.values[0][0]}, " f"date: {date}")
            print("-----------------------------------------")
        # ADJUSTMENT OF SEASON START AND END AT THE BEGINNING OF THE SEASON
        if (
            (sum_obs_24 >= thr_con_24[pollen_type])
            and (sum_obs >= thr_con_120[pollen_type])
            and ctsum_stns < tthrs_stns
        ):
            change_tthrs[istation] = ctsum_stns - tthrs_stns
            if pollen_type != "POAC":
                change_tthre[istation] = ctsum_stns - tthrs_stns
            if verbose:
                print("Big data and below threshold")
        elif (
            (0 <= sum_obs_24 < thr_con_24[pollen_type])
            and (0 <= sum_obs < thr_con_120[pollen_type])
            and (tthrs_stns < ctsum_stns)
            and (0 < saisn_stns < 10)
        ):
            if pollen_type != "POAC" and ctsum_stns < tthre_stns:
                change_tthre[istation] = t_2m_stns * (date - jul_days_excl[pollen_type])
                change_tthrs[istation] = t_2m_stns * (date - jul_days_excl[pollen_type])
            else:  # case POAC
                if saisn_stns < saisl_stns:
                    change_tthrs[istation] = t_2m_stns * (
                        date - jul_days_excl[pollen_type]
                    )
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
                change_tthre[istation] += ctsum_stns - tthre_stns
            elif (
                (sum_obs_24 > thr_con_24[pollen_type])
                and (sum_obs > thr_con_120[pollen_type])
                and (tthre_stns > ctsum_stns > tthre_stns - t_2m_stns * 5 * date)
            ):
                if verbose:
                    print("Big data (end of season)")
                change_tthre[istation] += t_2m_stns * (
                    date - jul_days_excl[pollen_type]
                )
        else:  # POAC
            if (
                (0 <= sum_obs_24 < thr_con_24[pollen_type])
                and (0 <= sum_obs < thr_con_120[pollen_type])
                and (saisn_stns < saisl_stns < saisn_stns + 5)
            ):
                if verbose:
                    print("Low data (end of season) POAC")
                change_saisl[istation] = saisn_stns - saisl_stns
            elif (
                (sum_obs_24 > thr_con_24[pollen_type])
                and (sum_obs > thr_con_120[pollen_type])
                and (saisn_stns < saisl_stns < saisn_stns + 5)
            ):
                if verbose:
                    print("Big data (end of season) POAC")
                change_saisl[istation] = 1
        # FAILSAFE
        if change_tthrs[istation] > 0:
            change_tthrs[istation] = min(failsafe[pollen_type], change_tthrs[istation])
        elif change_tthrs[istation] <= 0:
            change_tthrs[istation] = max(-failsafe[pollen_type], change_tthrs[istation])
        if pollen_type != "POAC":
            if change_tthre[istation] > 0:
                change_tthre[istation] = min(
                    failsafe[pollen_type], change_tthre[istation]
                )
            elif change_tthre[istation] <= 0:
                change_tthre[istation] = max(
                    -failsafe[pollen_type], change_tthre[istation]
                )
        else:  # POAC
            if change_saisl[istation] > 0:
                change_saisl[istation] = min(7, change_saisl[istation])
            elif change_saisl[istation] <= 0:
                change_saisl[istation] = max(-7, change_saisl[istation])
        if verbose:
            print(
                f"Change tthrs is now {change_tthrs[istation]} ",
                f"Change tthre is now {change_tthre[istation]} ",
                f"Change saisl is now {change_saisl[istation]} ",
            )
            print("-----------------------------------------")
    return change_phenology_fields(change_tthrs, change_tthre, change_saisl)


def to_grib(inp, outp, dict_fields):
    """Output fields to a GRIB file.

    Args:
        inp: Location of the GRIB file which must contain at least the same
    fields as the ones in the dictionary that are to be outputted.
        outp: Location of the desired GRIB file
        dict_fields: Dictionary containing the fields to be outputted as
            { name : value }

    """
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
    """Get the pollen type from the variables in the xarray.DataSet.

    Args:
        ds: xarray.DataSet containing one pollen-related field.

    Returns:
        pollen_type: String from pollen_types.

    """
    pollen_types = ["ALNU", "BETU", "POAC", "CORY"]
    for var in ds:
        if var[:4] in pollen_types:
            return var[:4]
    return "Error: pollen type not recognized."
