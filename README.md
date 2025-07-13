# KG-MCQA

Experimental codes for KR 2025, [_KR in the Wild_ track](https://kr.org/KR2025/call_kr_in_the_wild.html) preprint paper, "Applying Relation Extraction to Graph Matching for Answering Multiple Choice Questions".
![alt text](image.png)

## Setup

### Create Environment

Run the following command to create conda environment with required libraries. It automatically installs the original package `kgraph`, which is defined under `./kgraph` in this repository.

```shell
conda env create -f environment.yml
conda activate kg-mcqa
```

You can reinstall `kgraph` as follows:

```shell
pip install --upgrade --no-deps --force-reinstall kgraph/
```

### Test

You can run a simple test with PyTest.

```shell
pytest ./kgraph
```

## Experiment

```shell
python mcqa.py [dataset_path] [re_method]
```

## Documentation

In order to generate docs for the `kgraph` package, please run the following command in `./docs`.

```shell
sphinx-apidoc -f -o source/ ../kgraph/
make html
```

## Contents

### Directories

- `kgraph`: Original package for handling proposed method.
- `scripts`
- `dataset`: Original MCQ dataset.
- `KG_cache`: Cache files of KG constructed from Wikipedia articles.
- `wikipedia`: Dowonloaded Wikipedia articles.

### Files

- `mcqa.py`
- `fever.py`
- `environment.yml`
