"""Utils for the command line tool."""
# Standard library
import logging

# Third-party
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import scipy.interpolate as interp  # type: ignore


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
    with open(file_data) as f:
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
        with open(file_data_mod) as f:
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


def interpolate(change_tune, ds, lat_stns, lon_stns, method="IDW"):
    nstns = len(lat_stns)
    stns_points = np.array([[lat_stns[i], lon_stns[i]] for i in range(nstns)])
    grid_points = np.array(
        [ds.latitude.values.flatten(), ds.longitude.values.flatten()]
    ).T
    if method == "griddata":
        tune_vec = interp.griddata(
            stns_points, change_tune, (ds.latitude.values, ds.longitude.values)
        )
    elif method == "RBF":
        tune_vec = interp.RBFInterpolator(
            stns_points, change_tune, kernel="thin_plate_spline"
        )(grid_points).reshape(ds.latitude.values.shape)
    elif method == "IDW":
        tune_vec = simple_idw(
            lat_stns,
            lon_stns,
            change_tune,
            ds.latitude.values.flatten(),
            ds.longitude.values.flatten(),
        ).reshape(ds.latitude.values.shape)
    elif method == "Bspline":
        Bspline = interp.interp2d(lat_stns, lon_stns, change_tune, kind="linear")
        tune_vec = np.array(
            [
                Bspline(i, j)
                for i, j in zip(
                    ds.latitude.values.flatten(), ds.longitude.values.flatten()
                )
            ]
        ).reshape(ds.latitude.values.shape)
    elif method == "COSMO":
        nstns = len(lat_stns)
        min_param = [3.389, 4.046, 7.738, 1.875]
        max_param = [0.235, 0.222, 0.216, 0.405]
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
        if len(dist.shape) == 3:
            tune_vec = np.maximum(
                np.minimum(
                    ds.ALNUtune.values
                    * np.sum(change_tune[:, np.newaxis, np.newaxis] / dist, axis=0)
                    / np.sum(1 / dist, axis=0),
                    min_param[ipollen],
                ),
                max_param[ipollen],
            )
        else:
            tune_vec = np.maximum(
                np.minimum(
                    ds.ALNUtune.values
                    * np.sum(change_tune[:, np.newaxis] / dist, axis=0)
                    / np.sum(1 / dist, axis=0),
                    min_param[ipollen],
                ),
                max_param[ipollen],
            )
    else:
        print("Error: Invalid method selected!")
    return tune_vec


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
        tune_stns = ds.ALNUtune.where(
            (np.abs(ds.longitude - lon_stns[istation]) < eps)
            & (np.abs(ds.latitude - lat_stns[istation]) < eps),
            drop=True,
        ).values[0][0]
        saisn_stns = ds.ALNUsaisn.where(
            (np.abs(ds.longitude - lon_stns[istation]) < eps)
            & (np.abs(ds.latitude - lat_stns[istation]) < eps),
            drop=True,
        ).values[0][0]
        if (
            (np.sum(array[:, istation]) <= 720)
            or (np.sum(array_mod[:, istation_mod]) <= 720)
            and saisn_stns > 0
        ):
            change_tune[istation] = (tune_pol_default / tune_stns) ** (1 / 24)
        if (
            (np.sum(array[:, istation]) > 720)
            and (np.sum(array_mod[:, istation_mod]) > 720)
            and saisn_stns > 0
        ):
            change_tune[istation] = (
                np.sum(array[:, istation]) / np.sum(array_mod[:, istation_mod])
            ) ** (1 / 24)
    return change_tune


def to_grib(field):
    # Todo
    print(field)
