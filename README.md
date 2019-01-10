# SourcetrailPythonIndexer
Python Indexer for Sourcetrail based on [jedi](https://github.com/davidhalter/jedi), [parso](https://github.com/davidhalter/parso) and [SourcetrailDB](https://github.com/CoatiSoftware/SourcetrailDB)


## CI Pipelines
Windows: [![Build status](https://ci.appveyor.com/api/projects/status/4vo082swmhmny1a1/branch/master?svg=true)](https://ci.appveyor.com/project/mlangkabel/sourcetrailpythonindexer/branch/master)


## Requirements
* [jedi 0.13.2](https://pypi.org/project/jedi/0.13.2)
* [parso 0.3.1](https://pypi.org/project/parso/0.3.1)
* [SourcetrailDB](https://github.com/CoatiSoftware/SourcetrailDB) for Python


## Setup
* Check out this repository
* Install jedi by running `pip install jedi`
* Download the [SourcetrailDB Python bindings](https://github.com/CoatiSoftware/SourcetrailDB/releases) for your specific Python version and extract both the `_sourcetraildb.pyd` (`_sourcetraildb.so` on unix) and the `sourcetraildb.py` files to the root of the checked out repository


## Running the Source Code
To index an arbitrary Python source file, execute the command:

```
$ python run.py --source-file-path=your/python/file.py --database-file-path=your/generated/database/file.srctrldb
```


## Executing the Tests
To run the tests for this project, execute the command:
```
$ python test.py
```
