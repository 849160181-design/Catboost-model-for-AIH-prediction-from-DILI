# Data availability

This repository contains **no patient-level data, pathology images, whole-slide images,
image metadata, or medical records**. It also does not contain the study's training,
internal-validation, or external-validation datasets, manuscript text, or article-level
result tables.

## Why the study data are not deposited

The withheld materials contain information that could lead to participant
re-identification — including image-level metadata, acquisition dates, institutional
identifiers, and rare histopathological patterns. The original informed-consent
documents and ethics approvals cover the study analyses only; they do not cover open
redistribution. Public deposition would exceed the scope of consent and may breach
applicable data-protection regulations. The data are therefore withheld in full, not
merely omitted from an otherwise open release.

## What is released

1. the locked CatBoost model (`model/catboost_model.cbm`), a dependency-free scorer,
   and a machine-readable model manifest;
2. the complete analysis code for the `01_qc → 02_quantification.ijm → 03_features →
   04_regression → 05_model → 06_thresholds → 07_subgroups → 08_figures` pipeline;
3. a fully synthetic demonstrator cohort of 180 rows whose fields match
   `data_dictionary.csv`, together with the generator script and a data note;
4. the data dictionary and the model card.

The synthetic cohort is **not** a de-identified copy of the study data. It is generated
from a transparent latent-class model with fixed seeds and is calibrated to produce a
realistic AUC for software verification. It must not be used to estimate clinical
performance, prevalence, or subgroup effects.

## Controlled access

Record-level study data may be made available only through a controlled-access route.
Requests from qualified researchers are reviewed by the data access committee and the
institutional review board. Where the original consent and ethics approval permit,
de-identified data may be shared under a data-use agreement that prohibits
re-identification, requires secure storage and an approved analysis plan, and requires
acknowledgement of the source. Requests should be addressed to the data access committee
at `[data-access email]`. This is a controlled-access route, not an open deposit; some
data may not be shareable at all where consent does not permit it.

## Manuscript statement

The full Data sharing statement, Methods–Reproducibility text, and reference 41 are
maintained in the private manuscript folder outside this repository. They are inserted
into the manuscript at the three required locations; they are not published here.
