"""
extract_utils.py — Nusawave Labs · extract-point
Reusable helpers for ERA5 and gridded NetCDF point extraction.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

DEFAULT_RENAME = {
    "swh": "hs_m",
    "tp": "tp_s",
    "mwd": "wave_dir_deg",
    "shts": "swell_hs_m",
    "mdts": "swell_dir_deg",
    "mpts": "swell_tp_s",
    "u10": "u10_ms",
    "v10": "v10_ms",
}

LAT_CANDIDATES = ("latitude", "lat", "y")
LON_CANDIDATES = ("longitude", "lon", "x")
TIME_CANDIDATES = ("time", "valid_time")
WAVE_VAR_CANDIDATES = ("swh", "Hs", "hs", "VHM0")


def find_data_file(*candidates: str | Path) -> Path:
    """Return the first existing path from candidates, or raise FileNotFoundError."""
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(
        f"None of the candidate paths exist: {[str(c) for c in candidates]}"
    )


def detect_dims(ds: xr.Dataset) -> tuple[str, str, str | None]:
    """Return (lat_dim, lon_dim, time_dim) from common naming conventions."""
    lat_dim = next((name for name in LAT_CANDIDATES if name in ds.dims or name in ds.coords), None)
    lon_dim = next((name for name in LON_CANDIDATES if name in ds.dims or name in ds.coords), None)
    time_dim = next((name for name in TIME_CANDIDATES if name in ds.dims), None)
    if lat_dim is None or lon_dim is None:
        raise ValueError(
            f"Could not detect lat/lon dims in {list(ds.dims)} / {list(ds.coords)}"
        )
    return lat_dim, lon_dim, time_dim


def detect_wave_var(ds: xr.Dataset, var: str | None = None) -> str:
    """Pick the primary wave-height variable for benchmarking."""
    if var and var in ds.data_vars:
        return var
    for name in WAVE_VAR_CANDIDATES:
        if name in ds.data_vars:
            return name
    if ds.data_vars:
        return next(iter(ds.data_vars))
    raise ValueError("No data variables found in dataset")


def extract_point(
    nc_path: str | Path,
    lat: float,
    lon: float,
    variables: list[str] | None = None,
    method: str = "nearest",
    chunks: dict | None = None,
    rename: dict[str, str] | None = DEFAULT_RENAME,
    lat_dim: str | None = None,
    lon_dim: str | None = None,
) -> pd.DataFrame:
    """
    Extract a time series at (lat, lon) from a NetCDF file.

    Parameters
    ----------
    nc_path   : Path to the NetCDF file.
    lat, lon  : Target coordinates (degrees).
    variables : Variable names to extract (default: all data vars).
    method    : 'nearest' or 'linear' (bilinear interpolation).
    chunks    : Dask chunks dict, e.g. {"time": 500}. None = no Dask.
    rename    : Column rename map applied after extraction. None = keep raw names.
    lat_dim   : Override latitude dimension name (auto-detected if None).
    lon_dim   : Override longitude dimension name (auto-detected if None).

    Returns
    -------
    pd.DataFrame indexed by datetime.
    """
    ds = xr.open_dataset(nc_path, chunks=chunks)
    detected_lat, detected_lon, _ = detect_dims(ds)
    lat_dim = lat_dim or detected_lat
    lon_dim = lon_dim or detected_lon
    variables = variables or list(ds.data_vars)

    if method == "linear":
        point = ds[variables].interp(**{lat_dim: lat, lon_dim: lon})
    else:
        point = ds[variables].sel(**{lat_dim: lat, lon_dim: lon}, method=method)

    drop_cols = [lat_dim, lon_dim, "number", "expver", "depth", "surface"]
    df = point.compute().to_dataframe().drop(columns=drop_cols, errors="ignore")
    df.index = pd.to_datetime(df.index)
    df.index.name = "datetime"

    if rename:
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    return df


def add_wind_speed(df: pd.DataFrame, u_col: str = "u10_ms", v_col: str = "v10_ms") -> pd.DataFrame:
    """Add wind_speed_ms and wind_dir_deg columns (meteorological convention)."""
    result = df.copy()
    result["wind_speed_ms"] = np.sqrt(result[u_col] ** 2 + result[v_col] ** 2)
    result["wind_dir_deg"] = (270 - np.degrees(np.arctan2(result[v_col], result[u_col]))) % 360
    return result


def quick_stats(df: pd.DataFrame, var: str) -> pd.Series:
    """Return key percentile statistics for a variable."""
    series = df[var].dropna()
    return pd.Series(
        {
            "mean": series.mean(),
            "std": series.std(),
            "p50": series.quantile(0.50),
            "p90": series.quantile(0.90),
            "p95": series.quantile(0.95),
            "p99": series.quantile(0.99),
            "max": series.max(),
            "n": len(series),
        },
        name=var,
    )
