# extract-point
### Stop Crashing Your Laptop: How to Extract ERA5 Point Data in Under 10 Seconds

**Part of [Nusawave Labs](https://nusawave-labs.github.io)**

## Quick Start (Google Colab)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nusawave-labs/extract-point/blob/main/notebooks/extract_point.ipynb)

1. Click **Open in Colab** above
2. **Runtime → Run all** (or run the first cell, then Run all)
3. Done — no terminal, no `git clone`, no CDS account

The notebook clones this repo, installs dependencies, and downloads the sample NetCDF from a [GitHub Release](https://github.com/nusawave-labs/extract-point/releases/tag/v0.1-data) automatically.

## Quick Start (local)

```bash
git clone https://github.com/nusawave-labs/extract-point.git
cd extract-point
wget -q -O data/era5_sample.nc \
  https://github.com/nusawave-labs/extract-point/releases/download/v0.1-data/era5_sample.nc
pip install -r requirements-notebook.txt   # tutorial only
# pip install -r requirements.txt        # + cartopy/cdsapi for maintainer scripts
jupyter notebook notebooks/extract_point.ipynb
```

Run the **Step 0** bootstrap cell if the sample file is missing.

## What You'll Learn
- Lazy vs eager loading (the concept that saves your RAM)
- sel vs isel vs interp — when to use each
- Performance benchmarks across 4 extraction engines
- Clean export to CSV for downstream analysis

## Data
Uses ERA5 reanalysis (ECMWF) — open access, free to download.
Pre-sliced sample (~120 MB) for hands-on work; pre-computed benchmark charts for large-file comparisons (see `data/benchmark/`).

## License
MIT — use freely, attribution appreciated.

© Nusawave Labs 2026
