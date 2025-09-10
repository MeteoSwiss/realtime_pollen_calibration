# Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS

# Distributed under the terms of the BSD 3-Clause License.

# SPDX-License-Identifier: BSD-3-Clause

"""Utils for the command line tool."""
# Standard library
import logging
import sys
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import eccodes  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import xarray as xr  # type: ignore


@dataclass
class Config:

    pov_infile: str = ""
    """ICON GRIB2 file including path containing the pollen fields:
                'tthrs', 'tthre' (for POAC, 'saisl' instead),
                'saisn', 'ctsum' and 'tune'.
    """

    pov_outfile: str = ""
    """ICON GRIB2 file including path of the desired output file."""

    t2m_file: str = ""
    """"ICON GRIB2 file including path containing T_2M."""

    const_file: str = ""
    """ICON GRIB2 file including path containing Longitudes (clon)
        and Latitudes (CLAT) of the unstructured ICON grid.
    """

    station_obs_file: str = ""
    """ATAB file including path containing the measured
       pollen concentrations at the stations.
    """

    station_mod_file: str = ""
    """ATAB file including path containing the modelled
       pollen concentrations at the stations.
    """

    hour_incr: int = 1


ObsModData = namedtuple(
    "ObsModData",
    ["data_obs", "coord_stns", "missing_value", "data_mod", "istation_mod"],
    defaults=[None, None],
)
HeaderData = namedtuple(
    "HeaderData", ["coord_stns", "missing_value", "stn_indicators", "n_header"]
)
ChangePhenologyFields = namedtuple(
    "ChangePhenologyFields", ["change_tthrs", "change_tthre", "change_saisl"]
)

pollen_types = ["ALNU", "BETU", "POAC", "CORY"]

# thr_con_24 and thr_con_120 are thresholds for sums of hourly observed
# pollen observations used to make sure that pollen calibration is only
# performed if pollen concentrations were high enough to ensure robust
# results of the pollen calibration.
# TODO: these numbers should go into the config file # pylint: disable=fixme
thr_con_24 = {"ALNU": 120, "BETU": 240, "POAC": 72, "CORY": 120}
thr_con_120 = {"ALNU": 360, "BETU": 720, "POAC": 216, "CORY": 360}

# failsafe is a limiter for the change applied to the phenological fields
# tthrs and tthre (and saisl for POAC instead of tthre). The purpose is
# to ensure the adaptation of tthrs and tthre is not too large.
# TODO: these numbers should go into the config file # pylint: disable=fixme
failsafe = {"ALNU": 1000, "BETU": 2500, "POAC": 6000, "CORY": 2500}

# jul_days_excl is the number of days since Dec. 1 to be excluded
# in the calculation of the temperature sum.
# These numbers have been determined using an optimization procedure
# minimizing the mean absolute error (= difference between the observed
# and the modelled start of flowering).
# The methods used are described in Pauling et al. (2014): Toward
# optimized temperature sum parameterizations for forecasting the
# start of the pollen season, Aerobiologia, 30, 10.1007/s10453-013-9308-0
# TODO: these numbers should go into the config file # pylint: disable=fixme
jul_days_excl = {"ALNU": 14, "BETU": 40, "POAC": 46, "CORY": 3}


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


def read_clon_clat(const_file):
    with open(const_file, "rb") as fh:
        clon, clat = None, None
        while True:
            # Get the next message
            rec = eccodes.codes_grib_new_from_file(fh)
            if rec is None:
                break
            short_name = eccodes.codes_get(rec, "shortName")
            # Extract longitude and latitude of the ICON grid
            if short_name == "CLON":
                clon = eccodes.codes_get_array(rec, "values")
            elif short_name == "CLAT":
                clat = eccodes.codes_get_array(rec, "values")

            # Delete the message
            eccodes.codes_release(rec)
    return clon, clat


def read_atab(
    pollen_type: str, file_obs_stns: str, file_mod_stns: str = "", verbose: bool = True
) -> ObsModData:
    # pylint: disable=too-many-locals
    """Read the pollen concentrations and the station locations from the ATAB files.

    Args:
        pollen_type: String describing the pollen type analysed.
        file_obs_stns: Location of the observation ATAB file.
        file_mod_stns: Location of the model ATAB file. (Optional)
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
            missing_value: Value considered as a missing value.
            stn_indicators: Used for correspondence between
            observed and modelled data.

        """
        lat_stns = np.array([])
        lon_stns = np.array([])
        missing_value = None
        stn_indicators = None
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
                if line.strip()[0:9] == "PARAMETER":
                    n_header = n
                    break
            coord_stns = list(zip(lat_stns, lon_stns))
        return HeaderData(coord_stns, missing_value, stn_indicators, n_header)

    headerdata = read_obs_header(file_obs_stns)
    data = pd.read_csv(
        file_obs_stns,
        header=headerdata.n_header,
        sep=r"\s+",
        parse_dates=[[1, 2, 3, 4, 5]],
    )
    data = data[data["PARAMETER"] == pollen_type].iloc[:, 2:].to_numpy()
    if file_mod_stns != "":
        stn_indicators_mod = None
        missing_value = None
        with open(file_mod_stns, encoding="utf-8") as f:
            for n, line in enumerate(f):
                if line.strip()[0:18] == "Missing_value_code":
                    missing_value = float(line.strip()[20:])
                if line.strip()[0:9] == "Indicator":
                    stn_indicators_mod = np.array(line.strip()[29:].split("         "))
                if line.strip()[0:9] == "PARAMETER":
                    n_header_mod = n
                    break
        istation_mod = get_mod_stn_index(headerdata.stn_indicators, stn_indicators_mod)
        data_mod = pd.read_csv(
            file_mod_stns,
            header=n_header_mod,
            sep=r"\s+",
            parse_dates=[[3, 4, 5, 6, 7]],
        )
        data_mod = data_mod[data_mod["PARAMETER"] == pollen_type].iloc[:, 4:].to_numpy()
        if missing_value in data_mod:
            print(
                "There is at least one missing value",
                f"in the model data file {file_mod_stns}.\n",
                "Please check the reason (fieldextra retrieval namelist?).",
                "No pollen calibration update is performed until this is fixed! ",
                "Pollen in ICON will still work, but calibration fields get ",
                "more and more outdated.",
            )
            sys.exit(1)
    else:
        data_mod = 0
        istation_mod = 0
    data = treat_missing(
        data, headerdata.missing_value, headerdata.stn_indicators, verbose=verbose
    )
    return ObsModData(
        data, headerdata.coord_stns, headerdata.missing_value, data_mod, istation_mod
    )


def create_data_arrays(cal_fields, clon, clat, time_values):
    # Dictionary to hold DataArrays for each variable
    cal_fields_arrays = {}

    # Loop through variables to create DataArrays
    for var_name, data in cal_fields.items():
        data_array = xr.DataArray(
            data, coords={"index": np.arange(len(data))}, dims=["index"]
        )
        data_array.coords["latitude"] = (("index"), clat)
        data_array.coords["longitude"] = (("index"), clon)
        data_array.coords["time"] = time_values
        cal_fields_arrays[var_name] = data_array
    return cal_fields_arrays


def treat_missing(
    array,
    missing_value: float = -9999.0,
    stn_indicators: str = "",
    verbose: bool = True,
):
    """Treat the missing values of the input array.

    Args:
        array: Array containing the concentration values.
        missing_value: Value considered as a missing value.
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
                f"Station {stn_indicators[istation]} has",
                f"{skip_missing_stn[istation]} missing values",
            )
        if skip_missing_stn[istation] > 0:
            if (
                np.count_nonzero(np.abs(array[:, istation] - missing_value) < 0.01)
                / len(array[:, istation])
                < 0.5
            ):
                idx1 = np.where(np.abs(array[:, istation] - missing_value) > 0.01)
                idx2 = np.where(np.abs(array[:, istation] - missing_value) < 0.01)
                if verbose:
                    print(
                        "Less than 50% of the data is missing, ",
                        f"mean of the rest is: {np.mean(array[idx1, istation])}",
                    )
                array[idx2, istation] = np.mean(array[idx1, istation])
            else:
                print(
                    f"Station {stn_indicators[istation]} has more than 50% missing ",
                    "data. Please check the reason (Does jretrievedwh still work?).\n",
                    "No pollen calibration update is performed until this is fixed! ",
                    "Pollen in ICON will still work, but calibration fields get ",
                    "more and more outdated.",
                )
                sys.exit(1)
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
):
    """Interpolate the change of a field from its values at the stations.

    Args:
        change: Value of the change at the stations.
        ds: xarray.DataSet.
        field: Name of the field to be interpolated on.
        coord_stns: List of (lat, lon) tuples of the stations' coordinates.
        method: Either 'multiply' (strength) or 'add' (phenology)
        verbose: Optional additional debug prints.

    Returns:
        vec: Obtained field over the full grid.
    This is a reproduction of the IDW implemented in COSMO.
    with different threshold (minima and maxima) for different species.

    """
    vec = None
    nstns = len(coord_stns)
    pollen_type = field[:4]
    if method == "multiply":
        # max_param and min_param are limiters for the change applied to the
        # tuning factor. The purpose is to ensure the adaptations are not too large.
        # TODO: these numbers should go into the config file # pylint: disable=fixme
        max_param = {"ALNU": 3.389, "BETU": 4.046, "POAC": 1.875, "CORY": 7.738}
        min_param = {"ALNU": 0.235, "BETU": 0.222, "POAC": 0.405, "CORY": 0.216}
    else:
        bigvalue = 1e10
        max_param = {
            "ALNU": bigvalue,
            "BETU": bigvalue,
            "POAC": bigvalue,
            "CORY": bigvalue,
        }
        min_param = {
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
                max_param[pollen_type],
            ),
            min_param[pollen_type],
        )
    elif method == "sum":
        vec = np.maximum(
            np.minimum(
                ds[field].values
                + np.sum(change_vec / dist, axis=0) / np.sum(1 / dist, axis=0),
                max_param[pollen_type],
            ),
            min_param[pollen_type],
        )
    return vec


def get_change_tune(  # pylint: disable=R0913
    pollen_type: str,
    obs_mod_data: ObsModData,
    ds,
    verbose: bool = False,
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
                f"Current pollen type is: {pollen_type}, ",
                f"Current station n°{istation}, ",
                f"(lat: {obs_mod_data.coord_stns[istation][0]}, ",
                f"lon: {obs_mod_data.coord_stns[istation][1]}), ",
                f"last 120H concentration observed: {sum_obs}, ",
                f"modeled: {sum_mod}",
            )
            print(
                f"Current tune value {tune_stns.values[0]} ",
                f"and saisn: {saisn_stns.values[0]}",
            )
        if saisn_stns > 0 and (
            sum_obs <= thr_con_120[pollen_type] or sum_mod <= thr_con_120[pollen_type]
        ):

            if verbose:
                print(
                    "Season started but low observation or modeled concentrations, "
                    "(tune)**(-1/24) = "
                    f"{(tune_pol_default / tune_stns.values[0]) ** (1 / 24)}"
                )
            change_tune[istation] = (tune_pol_default / tune_stns) ** (1 / 24)
        if (
            saisn_stns > 0
            and sum_obs > thr_con_120[pollen_type]
            and sum_mod > thr_con_120[pollen_type]
        ):
            if verbose:
                print(
                    "Season started and high observation ", "and modeled concentrations"
                )
            change_tune[istation] = (sum_obs / sum_mod) ** (1 / 24)
        if verbose:
            print(f"Change tune is now: {change_tune[istation]}")
            print("-----------------------------------------")
    return change_tune


def get_change_phenol(  # pylint: disable=R0912,R0914,R0915
    pollen_type: str, obs_mod_data: ObsModData, ds, verbose: bool = False
) -> ChangePhenologyFields:
    """Compute the change of the temperature thresholds for the plant phenology.

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
                f"Current pollen type is: {pollen_type}, ",
                f"Current station n°{istation}, ",
                f"(lat: {obs_mod_data.coord_stns[istation][0]}, ",
                f"lon: {obs_mod_data.coord_stns[istation][1]}), ",
                f"last 24H concentration observed: {sum_obs_24}, ",
                f"and last 120H {sum_obs}",
            )
            print(
                f"Cumulative temperature sum {ctsum_stns.values[0]} ",
                f"and threshold (start): {tthrs_stns.values[0]}",
                f" and saisn: {saisn_stns.values[0]}",
            )
            if pollen_type != "POAC":
                print(f"Cumsum temp threshold end: {tthre_stns.values[0]}")
            else:
                print(f"Saisl: {saisl_stns.values[0]}")
            print(f"Temperature at station {t_2m_stns.values[0]}, " f"date: {date}")
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
                print("High observed concentrations and below threshold")
        elif (
            (0 <= sum_obs_24 < thr_con_24[pollen_type])
            and (0 <= sum_obs < thr_con_120[pollen_type])
            and (tthrs_stns < ctsum_stns)
            and (0 < saisn_stns < 5)  # restrict adaptation to the first 5 days of the
            # season. TODO: move the number to the config file # pylint: disable=fixme
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
                print("Low observed concentrations and in first 10 days of season")
        # ADJUSTMENT OF SEASON END AT THE END OF THE SEASON
        if pollen_type != "POAC":
            if (
                (0 <= sum_obs_24 < thr_con_24[pollen_type])
                and (0 <= sum_obs < thr_con_120[pollen_type])
                and (
                    tthre_stns - t_2m_stns * 5 * (date - jul_days_excl[pollen_type])
                    < ctsum_stns
                    < tthre_stns
                )
            ):
                if verbose:
                    print("Low observed concentrations (end of season)")
                change_tthre[istation] += ctsum_stns - tthre_stns
            elif (
                (sum_obs_24 > thr_con_24[pollen_type])
                and (sum_obs > thr_con_120[pollen_type])
                and (
                    tthre_stns
                    > ctsum_stns
                    > tthre_stns - t_2m_stns * 5 * (date - jul_days_excl[pollen_type])
                )
            ):
                if verbose:
                    print("High observed concentrations(end of season)")
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
                    print("Low observed concentrations (end of season) POAC")
                change_saisl[istation] = saisn_stns - saisl_stns
            elif (
                (sum_obs_24 > thr_con_24[pollen_type])
                and (sum_obs > thr_con_120[pollen_type])
                and (saisn_stns < saisl_stns < saisn_stns + 5)
            ):
                if verbose:
                    print("High observed concentrations (end of season) POAC")
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
    return ChangePhenologyFields(change_tthrs, change_tthre, change_saisl)


def check_mandatory_fields(cal_fields, pol_fields, pov_infile):
    """Check if all mandatory fields for all species read are present.

    Args:
        cal_fields: Dictionary of calibration fields.
        pol_fields: Names of the pollen fields.
        pov_infile: GRIB2 file containing pollen fields.

    Exits:
        If any mandatory fields are missing.

    """
    species_read = {key[:4] for key in cal_fields.keys()}
    print(f"Species read in pov_infile: {species_read}")
    req_fields = [fld for fld in pol_fields if fld[:4] in species_read]
    print(f"Mandatory fields required for species: {req_fields}")  
    missing_fields = [fld for fld in req_fields if fld not in cal_fields.keys()]
    print(f"missing_fields from pov_infile: {cal_fields.keys()}")
    if missing_fields:
        print(
            f"The mandatory field(s): {missing_fields}\n",
            f"is/are missing in {pov_infile}\n"
            "No pollen calibration is done until this is fixed!\n"
            "Pollen are still calculated but this should be fixed "
            "within a few days.",
        )
        sys.exit(1)
    else:
        print("All mandatory fields have been read from pov_infile.")


def to_grib(inp: str, outp: str, dict_fields: dict, hour_incr: int) -> None:
    """Output fields to a GRIB file.

    Args:
        inp: Location of the GRIB file which must contain at least the same
            fields as the ones in the dictionary that are to be outputted.
        outp: Location of the desired GRIB file
        dict_fields: Dictionary containing the fields to be outputted as
            { name : value }
        hour_incr: number of hour increments in the output compared to input.

    """
    # copy all the fields from input into output,
    # besides the ones in the dictionary given as input
    with open(inp, "rb") as fin, open(outp, "wb") as fout:
        while True:
            gid = eccodes.codes_grib_new_from_file(fin)
            if gid is None:
                break
            # clone record
            clone_id = eccodes.codes_clone(gid)

            # get short_name
            short_name = eccodes.codes_get_string(clone_id, "shortName")

            # get time information, advance by hour_incr hours and
            # set the new time information
            data_date_hour = str(eccodes.codes_get(clone_id, "dataDate")) + str(
                str(eccodes.codes_get(clone_id, "hour")).zfill(2)
            )
            date_new = datetime.strptime(data_date_hour, "%Y%m%d%H") + timedelta(
                hours=hour_incr
            )

            eccodes.codes_set(
                clone_id, "dataDate", int(date_new.date().strftime("%Y%m%d"))
            )
            eccodes.codes_set(clone_id, "hour", int(date_new.time().strftime("%H")))

            # read values
            values = eccodes.codes_get_values(clone_id)

            if short_name in dict_fields:

                # set values in dict_fields[short_name] to zero where
                # values are zero (edge values)
                # This is because COSMO-1E was slightly smaller than ICON-CH1
                dict_fields[short_name][values == 0] = 0
                eccodes.codes_set_values(clone_id, dict_fields[short_name].flatten())
            else:
                eccodes.codes_set_values(clone_id, values)

            eccodes.codes_write(clone_id, fout)
            eccodes.codes_release(clone_id)
            eccodes.codes_release(gid)


def get_pollen_type(ds) -> list:
    """Get the pollen type from the variables in the xarray.DataSet.

    Args:
        ds: xarray.DataSet containing one pollen-related field.

    Returns:
        present_ptype: List of pollen types for which data
            is present in ds.

    """
    present_ptype = []
    for var in ds:
        if var[:4] in pollen_types and var[:4] not in present_ptype:
            present_ptype.append(var[:4])
    return present_ptype
