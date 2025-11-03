## [2.0.1] - 2025-11-03
### Fixed
- Resolved NoData-only outputs by hardening raster alignment prior to inference.
### Performance
- Reduced peak memory by building features on-the-fly only for valid pixels.
- More predictable parallelism with simplified thread controls.
- Chunked prediction to cap working-set size and stabilize runtime on large scenes.
- Correct distance truncation in channel-distance computations, lowering compute cost without loss of fidelity.

## [2.0.0] - 2025-10-24
### Breaking changes
- Susceptibility computation re-engineered using a Random Forest–based approach. Results are **not directly comparable** with v1.x.x.
### Added
- Module selection window: choose between the full **Risk** workflow (susceptibility + vulnerability; currently Brazil-only) or **Susceptibility-only** (available worldwide).
- Automatic DEM acquisition for the **largest hydrologically consistent extent** enclosing the user’s AOI, standardising HAND/MRVBF preprocessing.
### Changed
- HAND is now computed over the full extent to ensure hydrological consistency across the network.
- MRVBF resolution now remains constant regardless of AOI size (decoupled from analysis window scaling).
- More robust SAGA GIS invocation for MRVBF (more reliable `saga_cmd` discovery, environment handling, and clearer error messages).
### Performance
- Optimised stream-threshold calculation for the drainage network used in HAND — faster execution and lower RAM usage.
### Documentation
- README substantially expanded and reorganised for clarity and onboarding.
### Fixed
- Robust, locale-agnostic numeric parsing and aggregation of asset weight fields, ensuring accurate totals and thresholding in interdependence metrics.
- Consistent spatial alignment between vector inputs and the susceptibility raster prior to sampling, preventing misclassification and empty masks.
- Removed spurious/noisy warnings across the pipeline.


## [1.0.3] - 2025-09-20
### Documentation
- Corrected citation title in `CITATION.cff`.

## [1.0.2] - 2025-09-20
### Documentation
- Added concept DOI badge and “How to cite” section to README.
- Added concept DOI (DataCite/Zenodo) to `CITATION.cff`.
- Minor wording and structure improvements across the documentation.

## [1.0.1] - 2025-09-20
### Added
- First citable DOI release on Zenodo.
### Documentation
- Corrected `CITATION.cff` and improved metadata for Zenodo.
- README improvements (badges; installation notes for Earth Engine/SAGA).
- Added Windows DLL guidance.

## [1.0.0] - 2025-09-20
### Added
- First public, versioned release of PRIORI.