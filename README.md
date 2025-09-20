# PRIORI
A GIS-based framework for quantifying flood-related operational risk in road networks, integrating geomorphological indices, socioeconomic conditions, and critical infrastructure exposure.

## License
Apache License 2.0 — see `LICENSE` (and `NOTICE`).

## Citation

- Cite this software using the repository’s `CITATION.cff` (if present) and/or the DOI of the release archived on Zenodo.
- Cite external datasets (e.g., census, OSM, elevation models) according to their original licenses and attribution requirements.

---
# Initialization Guide

## 1) Environment (Conda)

This project ships an `environment.yml` using **conda-forge** (stable for the geospatial stack).  
To create/update:

```bash
# create
conda env create -f environment.yml
conda activate priori-conda

# update later if environment.yml changes
conda env update -f environment.yml -n priori-conda
```

**Tip (Windows):** prefer installing `gdal`, `rasterio`, `pyproj`, `geopandas`, `cartopy` via conda-forge (as in the YAML). Avoid `pip install` for those.

---

## 2) External dependency — SAGA GIS (CLI)

PRIORI uses the **MRVBF** tool from **SAGA GIS**. You need the **`saga_cmd`** CLI available on your system.

### Install SAGA GIS
- Use an official installer or a GIS distribution that includes SAGA (e.g., OSGeo4W on Windows), or the platform-specific installer.  
- Locate the **full path** to `saga_cmd`:
  - **Windows**: e.g. `C:\OSGeo4W64\bin\saga_cmd.exe` or the path where you installed SAGA.

### Tell PRIORI where `saga_cmd` is:
Set the `SAGA_CMD` environment variable:

- **Windows (PowerShell)**:
  ```powershell
  setx SAGA_CMD "C:\path\to\saga_cmd.exe"
  ```
  (restart your IDE/terminal after `setx`), or set it only for the current session:
  ```powershell
  $env:SAGA_CMD = "C:\path\to\saga_cmd.exe"
  ```

- **PyCharm (Run Configuration)**:  
  *Run → Edit Configurations… → Environment variables → Add:*  
  `SAGA_CMD = C:\path\to\saga_cmd.exe` *(or your system path)*

> The code attempts auto-discovery (common install locations), but setting `SAGA_CMD` is the most reliable.

---

## 3) Earth Engine (Service Account JSON)

PRIORI accesses Google Earth Engine (EE). You’ll need a **Service Account** and its **JSON key**.

**Steps (summary):**
1. Create/choose a Google Cloud project and **enable** the **Earth Engine API**.
2. Create a **Service Account** and generate a **JSON key** (download the file).
3. In Earth Engine, **grant the Service Account** access to the assets you will use.

**Usage in PRIORI:**  
At runtime, the program will ask for the Service Account **email** and prompt you to **select the `.json` key** file.

Example of EE JSON structure:
```json
{
  "type": "service_account",
  "project_id": "ee-yourproject",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service@ee-yourproject.iam.gserviceaccount.com",
  "client_id": "1234567890",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service%40ee-yourproject.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

---

## 4) Running

### Terminal
```bash
conda activate priori-conda
python PRIORI.py
```

### PyCharm
- Interpreter: your Conda env `.../envs/priori-conda/python.exe`
- *Run → Edit Configurations…*:
  - **Script path**: `<repo_root>/PRIORI.py`
  - **Working directory**: `<repo_root>`
  - **Environment variables**:
    - Add `SAGA_CMD` if required (see above).
    - If you face GDAL/PROJ DLL issues on Windows, add the variables from the next section.

---

## 5) Windows + GDAL/PROJ (DLL guidance)

If you see an error like `ImportError: DLL load failed while importing _gdal`, use **one** of the approaches below.

**Configure Run Configuration env vars (recommended for IDE users)**

Set these environment variables in your run configuration (replace with your env path):

- **Windows:**
  ```
  PATH=%CONDA_PREFIX%\Library\bin;%PATH%
  GDAL_DATA=%CONDA_PREFIX%\Library\share\gdal
  PROJ_LIB=%CONDA_PREFIX%\Library\share\proj
  ```

> **Avoid mixing** conda-forge geospatial packages with `pip install` for `gdal`, `rasterio`, `pyproj`, `geopandas`, `cartopy` on Windows.

---

## 6) Data (Large files)

If the repository stores large datasets via **Git LFS**:

```bash
git lfs install
git lfs pull
```

---

## 7) GUI (pywebview)

By default, `pywebview` may try a Qt backend. You have two options:

- **Lightweight (Windows)**: force Edge WebView2 without extra packages:
  ```python
  import os
  os.environ['PYWEBVIEW_GUI'] = 'edgechromium'
  import webview
  ```
- **Qt backend**: install `qtpy` + `pyqt` (already present if listed in `environment.yml`).

---

## 8) Troubleshooting (FAQ)

**`FileNotFoundError [WinError 2]` when running MRVBF**  
The `saga_cmd` executable was not found. Set `SAGA_CMD` to the full path (see “SAGA GIS” section).

**`pyogrio.errors.DataSourceError: ... .gpkg not recognized`**  
Confirm you have the **real** file (not a small Git LFS pointer).  
Use `git lfs pull` or download the dataset.

**`ImportError: DLL load failed while importing _gdal`**  
Add the env vars or the Windows snippet shown in “Windows + GDAL/PROJ”.

**Earth Engine authentication issues**  
Ensure you are using a **Service Account** JSON and that the Service Account has **permissions** to read the assets you reference.

---

## Acknowledgments

- Third-party icons and assets are listed in `NOTICE`.
- Trademarks and institutional logos belong to their respective owners. No trademark rights are granted by this project.
