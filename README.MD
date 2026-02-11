# stlf-datasets-evaluation-repro

This repository contains code and research artifacts accompanying the paper:

**Short-Term Load Forecasting: A Systematic Review of Datasets, Evaluation Practices, and Reproducibility Gaps**

It is intended to support transparent, reproducible analysis of the reviewed literature and to make derived review artifacts easy to reuse.

## Abstract

Short-term load forecasting (STLF) is undergoing a fundamental shift driven by renewable integration, flexible demand, and evolving consumption patterns. This paper provides a systematic review of STLF literature since 2020, critically examining datasets, task formulations, and evaluation methodologies. We identify significant gaps in spatial coverage and geographic representation across 40 publicly available datasets, while synthesizing prevalent covariates and preprocessing standards. Our analysis reveals systemic inconsistencies in validation protocols, information constraints, and metric selection, which compromise reproducibility and fail to capture operationally critical phenomena such as peaks and ramps. To address these gaps, we introduce three primary artifacts: (i) a comprehensive metadata repository of the surveyed literature; (ii) STLF-REP, a standardized reporting and evaluation checklist, and (iii) a strategic research roadmap designed to catalyze the development of data-efficient, decision-aware, and operationally-grounded forecasting frameworks.

## Contents

- Tools and scripts to curate the systematic review corpus (search results, screening decisions, and corpus snapshots).
- Utilities to normalize and deduplicate bibliographic records into a consistent metadata format.
- Structured extraction of key concepts from included studies (e.g., datasets, evaluation protocols, metrics, model classes, covariates, tuning practices, and reporting details).
- Generated outputs used for the manuscript (tables, figures, summary statistics).
- Reusable review artifacts, including:
  - a machine-readable export of the curated corpus metadata, and
  - a reporting & evaluation checklist for short-term load forecasting studies (e.g., **STLF-REP**).

```
- src/
  - survey-processing/
    # contains the code necessary to reproduce the survey including prisma, depduplication, plots, ...
  - paper/
    # Contains the latex code to reproduce the paper and any literature pile
```

## How to use

1. Review the paper to understand the scope, inclusion criteria, and terminology used in the extracted fields.
2. Use the repository to reproduce the metadata extraction and analysis steps that generate the manuscript’s results.
3. Use the exported metadata and checklist materials as a starting point for:
   - benchmarking new STLF methods under clearer evaluation protocols,
   - improving documentation for datasets and experimental setups, and
   - closing common reproducibility gaps identified by the review.

## Data and licensing notes

- For licensing check the NOTICE
- Some datasets referenced by the reviewed literature may require separate access or licenses; please check the original dataset and publisher terms.

## Citation

If you use this repository or its artifacts, please cite the paper:

```
Falkner, Dominik. *Short-Term Load Forecasting: A Systematic Review of Datasets, Evaluation Practices, and Reproducibility Gaps*. Manuscript (unsubmitted), 2026.
```

(FULL BIBTEX not available yet)

## Contact

For questions, issues, or contributions, please open a GitHub issue in this repository.
