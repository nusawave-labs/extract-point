#!/usr/bin/env python3
"""
Generate pre-computed benchmark charts for the tutorial notebook.

Maintainers run this locally with large ERA5 NetCDF files (not shipped to users).
Outputs land in data/benchmark/ and are committed to the repo.

Usage:
  python3 benchmarks/generate_assets.py
  python3 benchmarks/generate_assets.py --era5-large data/era5_benchmark_10yr.nc
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "benchmarks"))

from benchmark import run_benchmark, save_results  # noqa: E402
from extract_utils import find_data_file  # noqa: E402

BENCHMARK_DIR = ROOT / "data" / "benchmark"
DEFAULT_ERA5_LARGE = ROOT / "data" / "era5_benchmark_10yr.nc"
DEFAULT_SAMPLE = ROOT / "data" / "era5_sample.nc"

ERA5_LARGE_LAT = 4.0
ERA5_LARGE_LON = 108.0


def build_synthetic_large_era5(output: Path, repeats: int = 4) -> Path:
    """Stack the teaching sample along time to approximate a multi-year file (~450 MB)."""
    import xarray as xr

    sample = find_data_file(DEFAULT_SAMPLE)
    if output.exists() and output.stat().st_size > sample.stat().st_size * 1.5:
        print(f"Reusing existing large ERA5 file: {output}")
        return output

    print(f"Building synthetic large ERA5 ({repeats}× time stack) → {output}")
    try:
        with xr.open_dataset(sample) as ds:
            parts = []
            delta = ds.time[1] - ds.time[0]
            span = ds.time[-1] - ds.time[0] + delta
            for i in range(repeats):
                shifted = ds.assign_coords(time=ds.time + span * i)
                parts.append(shifted)
            merged = xr.concat(parts, dim="time")
            output.parent.mkdir(parents=True, exist_ok=True)
            merged.to_netcdf(output)
    except MemoryError:
        print("  MemoryError during synthesis — falling back to teaching sample for ERA5 benchmark")
        return sample
    print(f"  → {output.stat().st_size / 1e9:.2f} GB on disk")
    return output


def generate_era5_large(data_path: Path | None, out_dir: Path) -> None:
    path = data_path or DEFAULT_ERA5_LARGE
    if not path.exists():
        path = build_synthetic_large_era5(path)
    size_gb = path.stat().st_size / 1e9
    results = run_benchmark(path, ERA5_LARGE_LAT, ERA5_LARGE_LON, verbose=True)
    save_results(
        results,
        csv_path=out_dir / "era5_large_benchmark.csv",
        png_path=out_dir / "era5_large_benchmark.png",
        title=(
            f"Point Extraction Benchmark — ERA5 ({size_gb:.1f} GB)\n"
            f"Natuna Sea · 20×20 grid · Nusawave Labs"
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate tutorial benchmark assets.")
    parser.add_argument("--era5-large", type=Path, default=None, help="Large ERA5 NetCDF path")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=BENCHMARK_DIR,
        help="Output directory for PNG/CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    generate_era5_large(args.era5_large, args.out_dir)


if __name__ == "__main__":
    main()
