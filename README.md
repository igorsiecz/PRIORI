# PRIORI - Protocol for Road Infrastructure Operational Risk due to Inundation

[![Version](https://img.shields.io/github/v/tag/igorsiecz/PRIORI?label=version&sort=semver)](https://github.com/igorsiecz/PRIORI/releases)

*A GIS-based framework to quantify flood-related **operational risk** in road networks — integrating geomorphological susceptibility, multi‑criteria road vulnerability, and risk mapping.*

> **Project origin & funding**
>
> **PRIORI** was developed during the M.Sc. of **Igor Sieczkowski Moreira**, advised by **Prof. Lélio Antônio Teixeira Brito** and co-advised by **Prof. Fernando Dornelles**, within the **Graduate Program in Civil Engineering: Construction and Infrastructure (PPGCI)** at **Universidade Federal do Rio Grande do Sul (UFRGS), Brazil**. The research was supported by **CNPq** (Brazil’s National Council for Scientific and Technological Development), scholarship **process no. 131454/2023‑4**, under the **Academic Innovation Master’s** modality in partnership with **infraTest Prüftechnik GmbH (infraTest)**.

---

## Why PRIORI?

- **Data‑scarce ready.** Replaces unavailable hydrodynamics with **geomorphological proxies** (HAND & MRVBF) to estimate flood *hazzard*.
- **Road‑centric vulnerability.** Blends **social, economic, and functional** factors to score how critical a road segment is.
- **End‑to‑end workflow.** Pulls inputs from **Google Earth Engine**, and processes everything with the **conda‑forge geospatial stack**.
- **Reproducible & transparent.** Configuration is code‑first; all steps are documented for reuse and auditing.

> **Scope.** PRIORI targets **operational** risk (service disruption potential), not physical asset fragility modelling. It is ideal for **screening**, **planning**, and **prioritization** at municipal–regional scales.

---

## Table of Contents

1. [Quickstart](#quickstart)
2. [Installation](#installation)
   - [1) Clone the repo](#1-clone-the-repo)
   - [2) Create the Conda environment](#2-create-the-conda-environment)
   - [3) Install SAGA GIS (MRVBF)](#3-install-saga-gis-mrvbf)
   - [4) Configure Google Earth Engine (Service Account)](#4-configure-google-earth-engine-service-account)
3. [Data (Large Files via Git LFS)](#data-large-files-via-git-lfs)
4. [Running](#running)
5. [Windows GDAL/PROJ tips](#windows-gdalproj-tips)
6. [Troubleshooting (FAQ)](#troubleshooting-faq)
7. [Cite & License](#cite--license)
8. [Acknowledgments](#acknowledgments)
9. [Contributing](#contributing)

---

## Quickstart

```bash
# 1) clone
git clone https://github.com/<your-org-or-user>/PRIORI.git
cd PRIORI

# 2) conda env
conda env create -f environment.yml
conda activate priori-conda

# 3) (Windows) point PRIORI to SAGA CLI if needed
#    e.g., PowerShell:
setx SAGA_CMD "C:\Path\To\saga_cmd.exe"

# 4) pull only the census file you need (see Data section for options)
git lfs install --skip-smudge
git lfs pull --include="BR_Census.gpkg" --exclude=""

# 5) run
python PRIORI.py
```

---

## Installation

### 1) Clone the repo
```bash
git clone https://github.com/igorsiecz/PRIORI.git
cd PRIORI
```

### 2) Create the Conda environment
This project ships an `environment.yml` pinned to **conda‑forge** for a stable geospatial stack.

```bash
conda env create -f environment.yml
conda activate priori-conda

# later updates
conda env update -f environment.yml -n priori-conda
```

> **Tip (Windows):** install **gdal, rasterio, pyproj, geopandas, cartopy** from *conda‑forge* (as declared in the YAML). Avoid `pip install` for those packages on Windows to prevent DLL issues.

### 3) Install SAGA GIS (MRVBF)
PRIORI runs **MRVBF** via the **SAGA GIS** command line (`saga_cmd`).

- Install SAGA GIS (official installer or OSGeo4W on Windows).
- Find the full path to `saga_cmd` (e.g., `C:\OSGeo4W64\bin\saga_cmd.exe`).

Set the path so PRIORI can find it:

- **Windows (PowerShell, persistent):**
  ```powershell
  setx SAGA_CMD "C:\Path\To\saga_cmd.exe"
  ```
- **Current session only:**
  ```powershell
  $env:SAGA_CMD = "C:\Path\To\saga_cmd.exe"
  ```
- **PyCharm:** *Run → Edit Configurations → Environment variables* → add `SAGA_CMD` with the full path.

### 4) Configure Google Earth Engine (Service Account)
PRIORI reads some inputs from **Google Earth Engine (EE)**. Use a **Service Account** + **JSON key**.

**Steps (summary):**
1. In Google Cloud, create or select a project and **enable the Earth Engine API**.
2. Create a **Service Account** and **download** its **JSON key**.
3. In Earth Engine, **grant the Service Account** access to the assets you will use.

**At runtime**, PRIORI will ask for the **Service Account e‑mail** and prompt you to **select the JSON key** file.

Example JSON (keys shortened):
```json
{
  "type": "service_account",
  "project_id": "ee-yourproject",
  "private_key_id": "…",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service@ee-yourproject.iam.gserviceaccount.com",
  "client_id": "1234567890",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

---

## Data (Large Files via Git LFS)

This repository ships **large census geodata** using **[Git LFS](https://git-lfs.com/)**. You can download **only what you need**.

### Available LFS artifacts
- `BR_Census.gpkg` — Brazilian census package

### Download everything (default)
```bash
git lfs install
git lfs pull
```

### Download selectively (recommended)
1) Prevent auto‑downloading on clone:
```bash
git lfs install --skip-smudge
```
2) Pull just the target file(s):
```bash
git lfs pull --include="file_name" --exclude=""
```

> **Naming convention.** Files may follow the pattern **`CC_Census.gpkg`**, where **`CC`** is the **ISO 3166‑1 alpha‑2 country code** (e.g., `BR` for Brazil, `US` for United States). 

> **Tip:** If you cloned earlier without `--skip-smudge`, run `git lfs fetch --include="BR_Census.gpkg" --exclude="" && git lfs checkout BR_Census.gpkg` to hydrate a single file locally.

---

## Running

### Terminal
```bash
conda activate priori-conda
python PRIORI.py
```

### PyCharm
- **Interpreter:** your Conda env `…/envs/priori-conda/python.exe`
- **Run → Edit Configurations:**
  - **Script path:** `<repo_root>/PRIORI.py`
  - **Working directory:** `<repo_root>`
  - **Environment variables:**
    - `SAGA_CMD` (if not on PATH)
    - On Windows, consider adding the GDAL/PROJ variables below if you hit DLL errors.

---

## Windows GDAL/PROJ tips

If you see `ImportError: DLL load failed while importing _gdal` or similar, set the following **Run Configuration env vars** (adjusting to your env path):

```
PATH=%CONDA_PREFIX%\Library\bin;%PATH%
GDAL_DATA=%CONDA_PREFIX%\Library\share\gdal
PROJ_LIB=%CONDA_PREFIX%\Library\share\proj
```

> Also avoid mixing conda‑forge geospatial packages with `pip install` counterparts on Windows.

---

## Troubleshooting (FAQ)

**`FileNotFoundError [WinError 2]` when running MRVBF**  
`SAGA_CMD` not found. Set it to the full path (see *Install SAGA GIS*).

**`.gpkg not recognized` / tiny file size**  
You likely have an **LFS pointer** instead of the real data. Run a selective `git lfs pull` for the specific file.

**Earth Engine authentication fails**  
- Make sure you’re using a **Service Account JSON** (not OAuth user token).
- Ensure the Service Account has **read permissions** to every referenced asset.

**Long‑running MRVBF on large rasters**  
- Consider tiling inputs or running on a higher‑performance machine.
- Verify your SAGA version; newer builds may be faster and more stable.

---

## Cite & License

- **License:** Apache License 2.0 — see `LICENSE` (and `NOTICE`).
- **How to cite:** Use the repository’s `CITATION.cff` and/or the DOI of the archival release. Also cite external datasets (OSM, census, DEMs) per their original licenses and attribution.

**Software citation:**
> Moreira, I.S. (2025). PRIORI: A GIS‑based framework for flood‑related operational risk in road networks (Version 1.0.0) \[Software\]. GitHub. https://github.com/igorsiecz/PRIORI (and DOI of the archived release)

---

## Acknowledgments

- **CNPq** scholarship **131454/2023‑4** (Brazil).  
- **infraTest Prüftechnik GmbH (infraTest)** for the Academic Innovation partnership.  
- UFRGS **PPGCI** graduate program and **LAPAV** lab community.  
- Open‑source ecosystems: **conda‑forge**, **GDAL**, **PROJ**, **SAGA GIS**, **Rasterio**, **GeoPandas**, **pyogrio**, **OSMnx**, **WhiteboxTools**, and **Google Earth Engine**.

---

## Contributing

Contributions are welcome! Please open an issue for bugs, feature requests, or documentation improvements.  
For pull requests, follow conventional commits if possible and keep PRs focused and small.

---

### Appendix — Commands you might need

**Update your fork/branch:**
```bash
git pull --rebase origin main
```

**Only (re)hydrate one LFS file you already fetched:**
```bash
git lfs checkout BR_Census.gpkg
```

**Update environment after YAML changes:**
```bash
conda env update -f environment.yml -n priori-conda
```
