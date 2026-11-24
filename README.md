# Was there more snow back then?

**Report: https://justinthebergejr.github.io/snowfall-hw/**

A reproducible test of whether New England had less annual snowfall in
**2000–2019** than in **1940–1999**, using NOAA's Global Historical Climatology
Network–Daily (GHCN-Daily). The report includes a yes/no answer, graphs,
station-level evidence, uncertainty intervals, sensitivity checks, and limitations.

**Answer: No, for this snowfall comparison.** The 21-station, equally
state-weighted index is **9.0% higher** in 2000–2019. The five-year-block 95%
bootstrap interval is **−1.1% to +20.9%**, so the observed increase is not
clearly distinguishable from variability. This does not rule out less snow
at a particular address, or less time with snow on the ground.

## Reproduce

Python **3.11 or later**, no third-party packages:

```sh
python scripts/analyze.py
python -m unittest discover -s tests
python -m http.server 8000 --directory docs
```

Open http://localhost:8000. Downloading requires an internet connection.
The analysis fetches station metadata, inventory, version, and individual daily
station files directly from [NOAA](https://www.ncei.noaa.gov/pub/data/ghcn/daily/).
Downloads are cached under ignored `data/`; subsequent runs reuse that snapshot.
To obtain a new snapshot, remove **only that local cache** and rerun. NOAA can revise
historical observations, so fresh results need not be byte-identical to this report.

## Analysis design

- Six states: CT, MA, ME, NH, RI, VT.
- Measure: calendar-year **SNOW**, not snow depth, water equivalent, or snow-cover duration.
- Candidate inventory endpoints: first SNOW year ≤1960, last ≥2013, necessary
  for the usable-year counts below.
- Reject missing/negative values and nonblank NOAA quality flags; trace = 0 mm.
- Require ≥95% valid daily observations **in every month** of an accepted year.
  Do not impute or scale missing days. Convert mm to inches with 25.4 mm/inch.
- Require ≥40 accepted years in 1940–1999 and ≥14 in 2000–2019.
- Compare means within each station. Average station percent changes within
  states; give each state equal weight. This is a **station-based relative index**,
  not an area-weighted estimate of total regional snowfall.
- Bootstrap years jointly across stations, separately by era: 5,000 replicates,
  fixed seeds, both individual years and circular five-year blocks.
- Sensitivity: 90%, 95%, and 100% monthly coverage. Panels are reselected;
  a regional result requires all six states.

An initial stricter start-date/year-count screen left some states unrepresented.
The coverage rules were revised before calculating a regional result; the report
discloses this. No station was selected based on the sign of its change.

## Repository layout

| Path | Purpose |
| --- | --- |
| `scripts/analyze.py` | Download, quality control, aggregation, uncertainty, small evidence exports |
| `scripts/publish.py` | Push reviewed commits and configure Pages via the GitHub API |
| `tests/test_analysis.py` | Synthetic tests for parsing, units, coverage, state weighting |
| `docs/` | Publication source: HTML, CSS, JavaScript; no build system |
| `docs/assets/results.json` | Small computed summary driving the report and graphs |
| `docs/assets/station-years.csv` | Small, auditable accepted annual observations |
| `docs/assets/manifest.json` | SHA-256 hashes and sizes of downloaded inputs |
| `data/` | Ignored raw download cache; never committed |

The files in `docs/assets/` are intentionally published evidence, not raw daily
downloads or disposable build artifacts. Graphs are rendered as accessible SVGs
in the browser. No dependency directory, site build output, or large data file
belongs in this repository.

## Deployment

GitHub repository **Settings → Pages → Deploy from a branch → main → /docs**.
The site has a `.nojekyll` file and needs no compilation.
After committing reviewed changes, an authenticated maintainer can instead run:

```sh
python scripts/publish.py
```

This uses the existing Git credential manager, does not log or persist secrets,
and requires permission to administer Pages. GitHub may take a few minutes to deploy.

## Sources

- [GHCN-Daily overview](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily)
- [NOAA format/flags documentation](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt)
- Menne et al. (2012), *An Overview of the Global Historical Climatology
  Network-Daily Database*. [doi:10.1175/JTECH-D-11-00103.1](https://doi.org/10.1175/JTECH-D-11-00103.1).
- Menne et al. (2012), *GHCN-Daily, Version 3*. NOAA NCDC.
  [doi:10.7289/V5D21VHZ](https://doi.org/10.7289/V5D21VHZ).
  Exact snapshot version, retrieval date, and input hashes are in the report assets.
