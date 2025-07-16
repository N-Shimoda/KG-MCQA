<h1 align="center">KG-MCQA</h1>

<p align="center">Source codes for KR 2025 workshop preprint<br>
<b>"Applying Relation Extraction and Graph Matching to Answering Multiple Choice Questions"</b>
<br>which is submitted to <a href="https://jurisinformaticscenter.github.io/NeLaMKRR2025/">NeLaMKRR 2025.</a></p>

This repository contains:

1. Python scripts for the answering experiment using the proposed method
1. Original MCQ datasets
1. Simple web application for visualizing the results

![Appearance of the web application](assets/app-appearance.png)

## Setup

### Create Environment

Run the following command to create conda environment with required libraries. It automatically installs the original package `kgraph`, which is defined under `./kgraph`.

```shell
conda env create -f environment.yml
conda activate kg-mcqa
```

### Activate web application

`./viewer` directory contains [Streamlit](https://streamlit.io/) app for viewing datasets and visualizing experimental results.
While running the following command, you can access to the app using web browser via [localhost:8501](http://127.0.0.1:8501).

```shell
streamlit run viewer/main.py
```

## Experiment

### Run all experiments

### Single run

Execute following command to run MCQA on a dataset using one of the RE methods.

```shell
python mcqa.py [dataset_path] [re_method]
```

Choose the `re_method` argument from the following.
| id | Model name | Dataset | Relation types |
|-------------|--------------------|---------|------------|
| `rebel` | REBEL | REBEL | 220 |
| `mrebel` | mREBEL$_400$ | RED$^{FM}$ | 400 |
| `mrebel_32` | mREBEL$_32$ | SRED$^{FM}$ | 32 |
| `unirel` | UniRel | NYT | 24 |

## Files & Directories

### Files

- `mcqa.py`
- `fever.py`
- `environment.yml`

### Directories

- `kgraph`: Original package for handling proposed method.
- `scripts`
- `dataset`: Original MCQ dataset.
- `KG_cache`: Cache files of KG constructed from Wikipedia articles.
- `wikipedia`: Dowonloaded Wikipedia articles.
