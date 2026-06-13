# Stop Crashing Your Laptop: Extract Any Point from ERA5 in Under 10 Seconds

You're a metocean engineer. Your client needs wave height time series at an offshore platform location — 4°N, 108°E, Natuna Sea. Someone hands you a 40-year ERA5 global file. Your laptop has 8GB RAM. What do you do?

## Project Structure

```bash
extract-point/
│
├── README.md                  ← repo landing page + quick start
├── LICENSE                    ← MIT
├── requirements.txt           ← pinned versions
├── notebooks/
│   └── extract_point.ipynb    ← THE main Colab notebook
│
├── data/
│   └── README.md              ← instructions to download ERA5 slice
│   └── era5_sample.nc         ← pre-sliced <10MB dummy file
│
├── src/
│   └── extract_utils.py       ← reusable functions (importable)
│
└── benchmarks/
    └── benchmark_results.png  ← pre-generated comparison chart
    └── benchmark.py           ← reproducible benchmark script
```