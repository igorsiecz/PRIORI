<p align="center">
  <img src="Icons/white_logo.png" alt="PRIORI Logo" height="110">
</p>

<h1 align="center">Protocol for Road Infrastructure Operational Risk due to Inundation</h1>
<h5 align="center">A GIS-based framework to assess flood-related operational risk in road networks.</h5>

<p align="center">
  <a href="https://github.com/igorsiecz/PRIORI/releases"><img src="https://img.shields.io/github/v/tag/igorsiecz/PRIORI?label=version&sort=semver&cacheSeconds=120" alt="Version"></a>&nbsp;
  <a href="https://doi.org/10.5281/zenodo.17168269"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.17168269.svg" alt="DOI"></a>&nbsp;
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white" alt="Python Version">&nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
</p>

---

<h2 align="center">About the Developer</h2>

<p align="center">
  <img src="Icons/igor_avatar.png" alt="Igor Moreira" width="160" style="border-radius:50%; margin-top:10px;">
</p>

<h3 align="center">Eng. Igor Sieczkowski Moreira</h3>

<h5 align="center">
  <b>M.Sc. Candidate in Civil Engineering (PPGCI – UFRGS)</b><br>
  <b>B.Sc. Civil Engineering (UFRGS) | Member of the LAPAV Laboratory</b><br>
</h5>

<h6 align="center" style="max-width:700px; margin:auto; font-size:14px;">
  Researcher focused on data science applications, flood and temperature effects on flexible pavements, and Python-based tools for infrastructure resilience analysis.
</h6>

<p align="center">
  <a href="https://www.instagram.com/igorsiecz/"><img src="https://img.shields.io/badge/Instagram-%23E4405F.svg?&style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram"></a>&nbsp;
  <a href="https://www.linkedin.com/in/igor-moreira-87a581286/"><img src="https://img.shields.io/badge/LinkedIn-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>&nbsp;
  <a href="http://lattes.cnpq.br/1013962464063766"><img src="https://img.shields.io/badge/Lattes-%23004A77.svg?&style=for-the-badge&logo=cnpq&logoColor=white" alt="Lattes CNPq"></a>
</p>

---

<h6 align="center">
  Developed at the <b>Pavement Laboratory (LAPAV)</b> of the <b>Federal University of Rio Grande do Sul (UFRGS)</b>, Brazil, 
  as part of the Master’s research within the <b>Graduate Program in Civil Engineering: Construction and Infrastructure (PPGCI)</b>.  
  Supported by <b>CNPq</b> (process <b>131454/2023-4</b>) under the <b>Academic Innovation Master’s Program (MAI/CNPq)</b>, 
  in partnership with <b>infraTest Prüftechnik GmbH</b>, and supervised by <b>Prof. Lélio Antônio Teixeira Brito</b> (advisor) 
  and <b>Prof. Fernando Dornelles</b> (co-advisor).
</h6>

---

<h2 align="center">📘 Table of Contents</h2>

<p align="center" style="font-size:16px; line-height:1.7;">
  <a href="#how-to-cite--license">How to Cite & License</a> •
  <a href="#the-priori-framework">The PRIORI Framework</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#installation">Installation</a> •
  <a href="#troubleshooting-faq">Troubleshooting (FAQ)</a> •
  <a href="#acknowledgments">Acknowledgments</a>
</p>

---

<a id="how-to-cite--license"></a>
<h2 align="center">📄 How to Cite & License</h2>

<p align="center" style="font-size:15px; line-height:1.6;">
  If you use <b>PRIORI</b> in your research, please cite the official archived release:
</p>

<h3 align="left" style="margin-top:40px;">📄 Standard Citation</h3>
<h4>
Moreira, I. S. (2025). PRIORI – Protocol for Road Infrastructure Operational Risk due to Inundation. Zenodo. https://doi.org/10.5281/zenodo.17168269
</h4>

### 📘 **BibTeX format**
```bibtex
@software{moreira_2025_17168269,
  author       = {Moreira, Igor Sieczkowski},
  title        = {PRIORI – Protocol for Road Infrastructure Operational Risk due to Inundation},
  year         = {2025},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.17168269},
  url          = {https://doi.org/10.5281/zenodo.17168269}
}
```

<h3 align="left">⚖️ License</h3>
This project is released under the <b>Apache License 2.0</b>.  
See the <a href="LICENSE"><code>LICENSE</code></a> file for full terms.

---

<a id="the-priori-framework"></a>
<h2 align="center">🌐 The PRIORI Framework</h2>

<p align="center" style="font-size:15px; line-height:1.7; max-width:850px; margin:auto;">
<b>PRIORI</b> (<i>Protocol for Road Infrastructure Operational Risk due to Inundation</i>) 
is a <b>GIS-based framework</b> designed to quantify <b>flood-related operational risk</b> in road networks.  
It integrates <b>geomorphological susceptibility</b>, <b>multi-criteria vulnerability</b>, and <b>exposure mapping</b> into an automated and transparent workflow for risk evaluation.  
<b>PRIORI</b> targets <b>operational risk</b> — the potential for <b>service disruption</b> — rather than physical asset fragility modelling.  
It is ideal for <b>screening, planning,</b> and <b>prioritization</b> at municipal to regional scales.
</p>

<h3 align="left" style="margin-top:35px;">🧭 Why it matters</h3>

<p align="left" style="font-size:15px; line-height:1.7; max-width:850px; margin:auto;">
In data-scarce contexts, <b>PRIORI</b> replaces unavailable hydrodynamic simulations with geomorphological proxies 
(<b>HAND</b> & <b>MRVBF</b>) to estimate flood susceptibility.  
Its <b>road-centric vulnerability model</b> blends <b>social, economic, and functional</b> indicators 
to measure how critical a road segment is for local accessibility and regional connectivity.
</p>

<h3 align="left" style="margin-top:35px;">⚙️ Core principles</h3>

<ul style="font-size:15px; line-height:1.8; max-width:850px; margin:auto;">
  <li><b>Data-scarce ready</b> — uses geomorphological proxies when hydrodynamic data are missing.</li>
  <li><b>End-to-end workflow</b> — integrates the <b>conda-forge geospatial stack</b> and <b>Google Earth Engine</b> for reproducibility.</li>
  <li><b>Transparent & auditable</b> — configuration is code-first, ensuring full traceability of results.</li>
  <li><b>Research-driven</b> — designed for open, modular, and scalable adaptation across contexts.</li>
</ul>

---

<a id="quickstart"></a>
<h2 align="center">⚡ Quickstart</h2>

<p align="center" style="font-size:15px; line-height:1.9; max-width:1000px; margin:auto; margin-bottom:25px;">
Get started with <b>PRIORI</b> in just a few steps — from cloning to running your first analysis.
</p>

<div style="max-width:1000px; margin:0 auto;">
<table style="width:100%; border-collapse:collapse; font-size:15px; line-height:1.8; text-align:left;">
  <tr style="background-color:rgba(255,255,255,0.05);">
    <td style="padding:15px 25px;">
      💾 <b style="font-size:18px;">1. Clone the repository</b><br>
      <code>git clone https://github.com/igorsiecz/PRIORI.git && cd PRIORI</code><br>
      Clone the latest version of the repository to your local machine.
    </td>
  </tr>
  <tr>
    <td style="padding:15px 25px;">
      🧩 <b style="font-size:18px;">2. Create and activate the Conda environment</b><br>
      <code>conda env create -f environment.yml && conda activate priori-conda</code><br>
      Installs all dependencies using the pinned <b>conda-forge</b> geospatial stack.
    </td>
  </tr>
  <tr style="background-color:rgba(255,255,255,0.05);">
    <td style="padding:15px 25px;">
      🗺️ <b style="font-size:18px;">3. Set up SAGA GIS (for MRVBF)</b><br>
      Ensure <code>saga_cmd</code> is installed and accessible.<br>
      On Windows (PowerShell):<br>
      <code>setx SAGA_CMD "C:\Path\To\saga_cmd.exe"</code>
    </td>
  </tr>
  <tr>
    <td style="padding:15px 25px;">
      🔐 <b style="font-size:18px;">4. Configure Google Earth Engine</b><br>
      Authenticate to Google Earth Engine with a <b>Service Account</b> using its JSON key: create a Google Cloud project, enable the <b>Earth Engine API</b>, create a service account, grant it viewer permissions, add the service-account email to your Earth Engine account, download the key (e.g., <code>service-account.json</code>), then point PRIORI to the file in the UI; see <a href="#installation">Installation</a> for the full step-by-step, permissions, and billing notes.
    </td>  
</tr>
  <tr style="background-color:rgba(255,255,255,0.05);">
    <td style="padding:15px 25px;">
      📦 <b style="font-size:18px;">5. Pull required datasets (Git LFS)</b><br>
      PRIORI stores geospatial data via <b>Git LFS</b>. Currently available artifact:<br>
      <ul style="margin-top:5px;">
        <li><code>BR_Census.gpkg</code> — Brazilian census package</li>
      </ul>
      Download it selectively:<br>
      <code>git lfs install --skip-smudge</code><br>
      <code>git lfs pull --include="BR_Census.gpkg" --exclude=""</code>
    </td>
  </tr>
  <tr>
    <td style="padding:15px 25px;">
      🚀 <b style="font-size:18px;">6. Run PRIORI</b><br>
      <code>python PRIORI.py</code><br>
      Launch the main interface and start analyzing flood-related operational risk.
    </td>
  </tr>
</table>
</div>

---

<a id="installation"></a>
<h2 align="center">🛠️ Installation</h2>

<table width="100%">

  <!-- 1) Clone -->
  <tr><td>
    <h3>1) Clone the repository</h3>
    <p>Download the PRIORI source code and move into the project folder.</p>
    <pre><code>git clone https://github.com/igorsiecz/PRIORI.git
cd PRIORI</code></pre>
  </td></tr>
  <tr><td><h6 align="center">Tip — If you already cloned it before, just run <code>git pull</code>.</h6></td></tr>

  <!-- 2) Conda env -->
  <tr><td>
    <h3>2) Create the Conda environment</h3>
    <p>
      Create and activate the environment using the provided <code>environment.yml</code>.
      This file already pins all packages from <b>conda-forge</b> (including <b>GDAL</b>,
      <b>PROJ</b>, <b>GeoPandas</b> and <b>Rasterio</b>), ensuring a stable and reproducible
      geospatial stack without additional manual configuration.
    </p>
    <pre><code>conda env create -f environment.yml
conda activate priori-conda</code></pre>
    <p>To update your environment later:</p>
    <pre><code>conda env update -f environment.yml -n priori-conda</code></pre>
  </td></tr>
  <tr><td><h6 align="center">Tip — You can use <code>mamba</code> instead of <code>conda</code> for faster solves (optional).</h6></td></tr>

  <!-- 3) SAGA GIS -->
  <tr><td>
    <h3>3) Install SAGA GIS</h3>
    <p>
      PRIORI relies on the <b>SAGA GIS</b> command-line tool <code>saga_cmd</code> for terrain
      indices such as MRVBF. On Windows, installation is easiest through the
      <b>OSGeo4W</b> framework, which provides the required libraries for GDAL/PROJ integration.
    </p>

  <ol>
    <li>
      Install <a href="https://www.osgeo.org/projects/osgeo4w/">OSGeo4W</a>
      (select “Advanced Install”) — this sets up GDAL, PROJ and related dependencies system-wide.
    </li>
    <li>
      Then install
      <a href="https://sourceforge.net/projects/saga-gis/">SAGA GIS</a>
      (stand-alone or via OSGeo4W) and verify that
      <code>saga_cmd.exe</code> is accessible.
    </li>
  </ol>

  <p><b>Set the SAGA CMD path (Windows PowerShell):</b></p>
  <pre><code>setx SAGA_CMD "C:\OSGeo4W64\bin\saga_cmd.exe"</code></pre>
  <p><b>Current session only:</b></p>
  <pre><code>$env:SAGA_CMD = "C:\OSGeo4W64\bin\saga_cmd.exe"</code></pre>

  <div>
<p><b>💡 GDAL/PROJ on Windows</b></p>
<p>If you encounter <code>ImportError: DLL load failed</code> when importing GDAL-based libraries, add these variables in your Run Configuration or system environment:</p>
<pre><code>PATH=%CONDA_PREFIX%\Library\bin;%PATH%
GDAL_DATA=%CONDA_PREFIX%\Library\share\gdal
PROJ_LIB=%CONDA_PREFIX%\Library\share\proj
</code></pre>
      <p>Avoid mixing conda-forge geospatial packages with <code>pip</code> wheels on Windows to prevent binary conflicts.</p>
    </div>
  </td></tr>
  <tr><td><h6 align="center">Note — Paths may vary; set <code>SAGA_CMD</code> to your installed binary.</h6></td></tr>

  <!-- 4) Google Earth Engine -->
  <tr><td>
    <h3>4) Configure Google Earth Engine (Service Account)</h3>
    <p>
      PRIORI accesses DEMs and satellite assets from <b>Google Earth Engine (GEE)</b>.
      You must authenticate using a <b>Service Account</b> and its <b>JSON key</b>.
    </p>

  <ol>
    <li>
      Enable the <b>Earth Engine API</b> in a Google Cloud Project:
      <a href="https://developers.google.com/earth-engine/guides/access">Earth Engine access guide</a>
    </li>
    <li>
      Create a <b>Service Account</b> and download the <b>JSON key</b>:
      <a href="https://developers.google.com/earth-engine/guides/service_account">Service Account guide</a>
    </li>
    <li>
      Grant the Service Account appropriate IAM roles for Earth Engine access:
      <a href="https://cloud.google.com/iam/docs/roles-permissions/earthengine">IAM roles for Earth Engine</a>
    </li>
  </ol>

  <p>
    At runtime, PRIORI will request the Service Account e-mail and prompt you to select the corresponding JSON key file.
  </p>

  <p><b>Example JSON key:</b></p>
  <pre><code>{
  "type": "service_account",
  "project_id": "ee-yourproject",
  "private_key_id": "your_private_key_id",
  "private_key": "your_private_key",
  "client_email": "your-service@ee-yourproject.iam.gserviceaccount.com",
  "client_id": "0000000000",
  "token_uri": "https://oauth2.googleapis.com/token"
}</code></pre>
  </td></tr>
  <tr><td><h6 align="center">Note — Use a <b>Service Account</b> (not OAuth user auth).</h6></td></tr>

  <!-- 5) Data via Git LFS -->
  <tr><td>
    <h3>5) Get required data (via Git LFS)</h3>
    <p>
      PRIORI stores large geospatial datasets using <b>Git LFS</b>. You may download specific files
      instead of fetching all binaries.
    </p>
    <p><b>Currently available artifact:</b></p>
    <ul>
      <li><code>BR_Census.gpkg</code> — Brazilian census package</li>
    </ul>
    <p><b>Selective download:</b></p>
    <pre><code>git lfs install --skip-smudge
git lfs pull --include="BR_Census.gpkg" --exclude=""</code></pre>
    <p>
      If you cloned without <code>--skip-smudge</code>, hydrate it manually:<br>
      <code>git lfs fetch --include="BR_Census.gpkg" --exclude="" && git lfs checkout BR_Census.gpkg</code>
    </p>
  </td></tr>
  <tr><td><h6 align="center">Note — LFS is only needed for large artifacts (e.g., census packs).</h6></td></tr>

  <!-- 6) Verify & run -->
  <tr><td>
    <h3>6) Verify and Run</h3>

  <p>Check that your environment is correctly configured:</p>
  <pre><code>python -c "import geopandas, rasterio, pyproj; print('All right!')"</code></pre>

  <p>
    Once dependencies are confirmed, launch PRIORI:
  </p>
  <pre><code>python PRIORI.py</code></pre>

  <p>
    When first launched, <b>PRIORI</b> will prompt for your <b>Google Earth Engine Service Account e-mail</b>
    and allow you to select the corresponding <code>.json</code> key file for authentication.
    After credentials are validated, the main <b>interactive interface</b> (built with <b>Tkinter</b>) opens.
    The home screen presents a <b>Start</b> button that launches the <b>Region of Interest (ROI)</b> selection window.
    Once the ROI is defined, PRIORI will ask which analysis modules should be executed:
  </p>

  <ul>
    <li><b>🌍 Full Risk Workflow:</b> performs both <i>susceptibility</i> and <i>vulnerability</i> analysis.  
        <small>(Currently limited to Brazil, where census and socioeconomic datasets are available.)</small></li>
    <li><b>🗺️ Susceptibility-only Workflow:</b> computes geomorphological susceptibility using <b>HAND</b> and <b>MRVBF</b>,  
        available globally — ideal for terrain screening or validation studies.</li>
  </ul>

  <p>
    Results are saved automatically in the project root, under a <code>/Results/</code> folder.
  </p>

  <p>
    You can also run PRIORI from <b>PyCharm</b> or another IDE.  
    Set your working directory to the repository root and ensure <code>SAGA_CMD</code> is defined in environment variables.
  </p>
  </td></tr>
  <tr><td><h6 align="center">Done — You’re all set to run PRIORI.</h6></td></tr>

</table>

---

<a id="troubleshooting-faq"></a>
<h2 align="center">⚠️ Troubleshooting (FAQ)</h2>

<table width="100%">

  <!-- 1) SAGA_CMD not found -->
  <tr><td>
    <h3><code>FileNotFoundError [WinError 2]</code> when running MRVBF</h3>
    <p><b>Cause:</b> The system cannot locate <code>saga_cmd.exe</code>.</p>
    <p><b>Solution:</b> Define the full path to your SAGA installation:</p>
    <pre><code>setx SAGA_CMD "C:\OSGeo4W64\bin\saga_cmd.exe"</code></pre>
    <p>Or for the current session only:</p>
    <pre><code>$env:SAGA_CMD = "C:\OSGeo4W64\bin\saga_cmd.exe"</code></pre>
  </td></tr>
  <tr><td><h6 align="center">Tip — After <code>setx</code>, restart terminal/IDE; on Linux/macOS ensure <code>saga_cmd</code> is in <code>PATH</code>.</h6></td></tr>

  <!-- 2) GDAL/PROJ DLL error -->
  <tr><td>
    <h3><code>ImportError: DLL load failed</code> for GDAL or Rasterio</h3>
    <p><b>Cause:</b> Windows cannot locate GDAL/PROJ libraries within the conda environment.</p>
    <p><b>Solution:</b> Add these environment variables to your IDE configuration or system settings:</p>
    <pre><code>PATH=%CONDA_PREFIX%\Library\bin;%PATH%
GDAL_DATA=%CONDA_PREFIX%\Library\share\gdal
PROJ_LIB=%CONDA_PREFIX%\Library\share\proj</code></pre>
    <p>Restart your terminal or IDE afterward to apply the changes.</p>
  </td></tr>
  <tr><td><h6 align="center">Note — Avoid mixing <code>pip</code> wheels with conda-forge; if issues persist, recreate the env from <code>environment.yml</code>.</h6></td></tr>

  <!-- 3) LFS pointer -->
  <tr><td>
    <h3><code>.gpkg</code> file is only a few kilobytes (LFS pointer)</h3>
    <p><b>Cause:</b> The file is just a Git LFS pointer, not the actual dataset.</p>
    <p><b>Solution:</b> Hydrate the file manually:</p>
    <pre><code>git lfs pull --include="BR_Census.gpkg" --exclude=""</code></pre>
    <p>If that fails, fetch and checkout explicitly:</p>
    <pre><code>git lfs fetch --include="BR_Census.gpkg" --exclude=""
git lfs checkout BR_Census.gpkg</code></pre>
  </td></tr>
  <tr><td><h6 align="center">Tip — Verify with <code>git lfs version</code>; if a network blocks LFS, try another connection or a mirror.</h6></td></tr>

  <!-- 4) EE authentication -->
  <tr><td>
    <h3>Earth Engine authentication fails</h3>
    <p><b>Cause:</b> The Service Account or JSON key is invalid, expired, or missing permissions.</p>
    <p><b>Solution:</b></p>
    <ul>
      <li>Ensure you are using a <b>Service Account JSON key</b> (not OAuth user token).</li>
      <li>Confirm that the Service Account has <b>read access</b> to required Earth Engine assets.</li>
      <li>If needed, regenerate the key via the <a href="https://developers.google.com/earth-engine/guides/service_account">Earth Engine Service Account console</a>.</li>
    </ul>
  </td></tr>
  <tr><td><h6 align="center">Note — Add the service account email to your EE project/assets and allow a few minutes for IAM to propagate.</h6></td></tr>

</table>

---

<a id="acknowledgments"></a>
<div align="center">
  <h2>Acknowledgments</h2>

  <p align="center">
    <sub>
      <b>CNPq</b> scholarship <b>131454/2023-4</b> (Brazil)
      &nbsp;●&nbsp;
      <b>infraTest Prüftechnik GmbH</b> (infraTest) — Academic Innovation partnership
      &nbsp;●&nbsp;
      <b>UFRGS PPGCI</b> graduate program &amp; <b>LAPAV</b> lab community
      &nbsp;●&nbsp;
      Open-source ecosystems: <b>conda-forge</b>, <b>GDAL</b>, <b>PROJ</b>, <b>SAGA GIS</b>, <b>Rasterio</b>, <b>GeoPandas</b>, <b>pyogrio</b>, <b>OSMnx</b>, <b>WhiteboxTools</b>, <b>Google Earth Engine</b>
    </sub>
  </p>

  <p align="center">
    <sub>© 2025 Igor S. Moreira — LAPAV / UFRGS</sub>
  </p>
</div>
