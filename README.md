# KG-MCQA

## Setup

1. Use following `conda` command for setting up basic environment.
   ```shell
   conda env create -f environment.yml
   ```
1. In order to install original package `kgraph`, run following `pip` command.
   ```shell
   pip install ./kgraph
   ```
   Be sure that the 3rd argument `./kgraph` specifies `kg-mcqa/kgraph` directory, not the `kgraph` library from PyPI.

## Test

You can run a simple test with PyTest.

```shell
pytest ./kgraph
```
