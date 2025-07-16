<h1 align="center">KG-MCQA</h1>

<p align="center">Source codes for KR 2025 workshop preprint<br>
<b>"Applying Relation Extraction and Graph Matching to Answering Multiple Choice Questions"</b>
<br>which is submitted to <a href="https://jurisinformaticscenter.github.io/NeLaMKRR2025/">NeLaMKRR 2025.</a></p>

This repository contains:

1. Python scripts for the answering experiment
1. Original MCQ datasets
1. Streamlit app for visualizing the results

## Setup

### Create Environment

Run the following command to create a conda environment with the required libraries. It automatically installs the original package `kgraph`.

```shell
conda env create -f environment.yml
conda activate kg-mcqa
```

### Activate Viewer

Activate [Streamlit](https://streamlit.io/) app for viewing datasets and experimental results.
While running the command, you can open the app in a browser via [localhost:8501](http://127.0.0.1:8501).

```shell
streamlit run viewer/main.py
```

![Appearance of the web application](assets/app-appearance.png)

## Experiment

> [!IMPORTANT]
> It is highly recommended to use GPUs to execute experiments.  
> The authors used an NVIDIA RTX 5000 Ada GPU with 32 GB RAM in the article.

### Run all experiments

The following script runs all the MCQAs introduced in the study.

```
./scripts/mcqa_main.sh
```

### Single experiment

To run a single MCQA using the specified RE method, use the next command.

```shell
python mcqa.py [dataset_path] [re_method]
```

Choices of `re_method` are as follows.
| `re_method` | Model name | Dataset | Relation types |
|-------------|--------------------|---------|------------|
| `rebel` | REBEL | REBEL | 220 |
| `mrebel` | mREBEL_400 | RED^{FM} | 400 |
| `mrebel_32` | mREBEL_32 | SRED^{FM} | 32 |
| `unirel` | UniRel | NYT | 24 |

### Baseline result by LLM

For the baseline experiment using Google's FLAN-T5-xlarge (3B) model, run the following script.

```shell
python llm.py
```

## Files & Directories

### Files

- `mcqa.py`
- `fever.py`
- `environment.yml`

### Directories

(ignored) shows the files not controlled by git.

- `kgraph`: Original package for handling the proposed method.
- `scripts`
- `dataset`: Original MCQ dataset.
- `exp-mcqa`: Result files of MCQA.
- `KG_cache`: Cache files of KG constructed from Wikipedia articles. (ignored)
- `wikipedia`: Downloaded Wikipedia articles. (ignored)
