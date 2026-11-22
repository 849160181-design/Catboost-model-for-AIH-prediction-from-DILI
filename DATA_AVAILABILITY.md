## Data availability

This repository contains no patient-level data, pathology images, whole-slide images or
medical records, and none of the datasets used to develop or validate the model.

### Why the data are not deposited

The withheld material contains information that could lead to participant
re-identification, including image metadata, acquisition dates, institutional identifiers
and rare histopathological patterns. The original informed-consent documents and ethics
approvals cover the analyses for which the samples were collected; they do not extend to
open redistribution. Public deposition would exceed the scope of consent and may breach
data-protection regulations, so the data are withheld in full.

### What is released

- the frozen CatBoost model (`model/catboost_model.cbm`), a dependency-free scorer and a
  machine-readable manifest;
- the complete analysis pipeline (`01_qc` to `08_figures`), including the ImageJ macro
  `02_quantification.ijm`;
- a synthetic demonstration cohort of 180 rows whose fields match
  `data_dictionary.csv`, with its generator and a data note;
- the data dictionary and the model card.

The synthetic cohort is not a de-identified copy of any study data. It is generated from
a transparent latent-class model with fixed seeds and is calibrated to give a realistic
AUC for software verification; it must not be used to estimate clinical performance,
prevalence or subgroup effects.

### Controlled access

Record-level data may be available only through a controlled-access route. Requests from
qualified researchers are reviewed by the data access committee and the institutional
review board; where the original consent and ethics approval permit, de-identified data
may be shared under a data-use agreement that prohibits re-identification, requires
secure storage and an approved analysis plan, and requires acknowledgement of the
source. Requests should be addressed to ⟨corresponding author email⟩. Some data may not
be shareable at all where consent does not permit it.
