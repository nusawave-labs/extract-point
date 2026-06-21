#!/usr/bin/env python3
"""Benchmark point extraction methods — time and peak RAM."""

from __future__ import annotations

import argparse
import sys
import time
import tracemalloc
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from extract_utils import detect_dims, detect_wave_var, find_data_file  # noqa: E402

DEFAULT_LAT = 4.0
DEFAULT_LON = 108.0
DEFAULT_CANDIDATES = (
    Path("data/era5_sample.nc"),
    Path("../data/era5_sample.nc"),
    Path("era5_sample.nc"),
)


def nearest_indices(
    nc_path: Path,
    lat: float,
    lon: float,
    *,
    lat_dim: str | None = None,
    lon_dim: str | None = None,
) -> tuple[int, int, str, str]:
    with xr.open_dataset(nc_path) as ds:
        lat_name, lon_name, _ = detect_dims(ds)
        lat_name = lat_dim or lat_name
        lon_name = lon_dim or lon_name
        lat_idx = int(np.abs(ds[lat_name].values - lat).argmin())
        lon_idx = int(np.abs(ds[lon_name].values - lon).argmin())
    return lat_idx, lon_idx, lat_name, lon_name


def measure(label: str, fn, *, verbose: bool = True) -> dict[str, float]:
    tracemalloc.start()
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {"time_s": elapsed, "peak_mb": peak / 1e6}
    if verbose:
        print(f"{label:25s}  {elapsed:.2f}s   peak RAM: {peak / 1e6:.1f} MB")
    return result


def run_benchmark(
    data_path: Path,
    lat: float,
    lon: float,
    *,
    interp_lat: float | None = None,
    interp_lon: float | None = None,
    var: str | None = None,
    lat_dim: str | None = None,
    lon_dim: str | None = None,
    time_chunk: int = 500,
    verbose: bool = True,
) -> dict[str, dict[str, float]]:
    lat_idx, lon_idx, lat_name, lon_name = nearest_indices(
        data_path, lat, lon, lat_dim=lat_dim, lon_dim=lon_dim
    )
    with xr.open_dataset(data_path) as ds:
        wave_var = detect_wave_var(ds, var)
        _, _, time_dim = detect_dims(ds)

    interp_lat = interp_lat if interp_lat is not None else lat + 0.12
    interp_lon = interp_lon if interp_lon is not None else lon + 0.37
    chunks = {time_dim: time_chunk} if time_dim else None

    results = {}
    results["Naive (full load)"] = measure(
        "Naive (full load)",
        lambda: xr.open_dataset(data_path, chunks=None)[wave_var].values[:, lat_idx, lon_idx],
        verbose=verbose,
    )
    results["xarray lazy + sel"] = measure(
        "xarray lazy + sel",
        lambda: xr.open_dataset(data_path)[wave_var]
        .sel(**{lat_name: lat, lon_name: lon}, method="nearest")
        .compute(),
        verbose=verbose,
    )
    results["xarray + Dask"] = measure(
        "xarray + Dask",
        lambda: xr.open_dataset(data_path, chunks=chunks)[wave_var]
        .sel(**{lat_name: lat, lon_name: lon}, method="nearest")
        .compute(),
        verbose=verbose,
    )
    results["xarray interp"] = measure(
        "xarray interp",
        lambda: xr.open_dataset(data_path)[wave_var]
        .interp(**{lat_name: interp_lat, lon_name: interp_lon})
        .compute(),
        verbose=verbose,
    )
    return results


def save_results(
    results: dict[str, dict[str, float]],
    *,
    csv_path: Path,
    png_path: Path,
    title: str = "Point Extraction Benchmark\nNusawave Labs · extract-point",
) -> None:
    import pandas as pd

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).T.to_csv(csv_path)

    labels = list(results.keys())
    times = [results[key]["time_s"] for key in labels]
    mems = [results[key]["peak_mb"] for key in labels]
    colors = ["#e74c3c", "#2ecc71", "#3498db", "#9b59b6"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    bars1 = ax1.bar(labels, times, color=colors, width=0.5)
    ax1.set_ylabel("Time (seconds)", fontsize=12)
    ax1.set_title("Extraction Speed", fontsize=13)
    for bar, val in zip(bars1, times):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{val:.2f}s",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    bars2 = ax2.bar(labels, mems, color=colors, width=0.5)
    ax2.set_ylabel("Peak RAM (MB)", fontsize=12)
    ax2.set_title("Memory Usage", fontsize=13)
    for bar, val in zip(bars2, mems):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{val:.0f} MB",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {csv_path}")
    print(f"Saved: {png_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark point extraction methods.")
    parser.add_argument("--data", type=Path, default=None, help="Path to NetCDF file")
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Target latitude")
    parser.add_argument("--lon", type=float, default=DEFAULT_LON, help="Target longitude")
    parser.add_argument("--var", type=str, default=None, help="Wave variable name (auto-detect)")
    parser.add_argument("--lat-dim", type=str, default=None, help="Latitude dimension name")
    parser.add_argument("--lon-dim", type=str, default=None, help="Longitude dimension name")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("benchmark_results.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=Path("benchmark_results.png"),
        help="Output plot path",
    )
    parser.add_argument("--title", type=str, default=None, help="Plot suptitle")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = args.data or find_data_file(*DEFAULT_CANDIDATES)
    results = run_benchmark(
        data_path,
        args.lat,
        args.lon,
        var=args.var,
        lat_dim=args.lat_dim,
        lon_dim=args.lon_dim,
    )
    title = args.title or f"Point Extraction Benchmark — {data_path.name}\nNusawave Labs · extract-point"
    save_results(results, csv_path=args.csv, png_path=args.png, title=title)


if __name__ == "__main__":
    main()
