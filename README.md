# KG-MCQA

## Setup

1. Use following `conda` command for setting up basic environment.
   ```shell
   conda env create -f environment.yml
   conda activate kg-mcqa
   ```
1. Please setup original package `kgraph` via local `pip` installation.
   ```shell
   pip install ./kgraph
   ```
   Be sure that the 3rd argument `./kgraph` specifies `kg-mcqa/kgraph` directory, not the `kgraph` library from PyPI.

## Test

You can run a simple test with PyTest.

```shell
pytest ./kgraph
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
