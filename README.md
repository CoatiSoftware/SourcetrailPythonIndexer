# SourcetrailPythonIndexer
Python Indexer for Sourcetrail based on jedi and SourcetrailDB


## CI Pipelines
Windows: [![Build status](https://ci.appveyor.com/api/projects/status/4vo082swmhmny1a1/branch/master?svg=true)](https://ci.appveyor.com/project/mlangkabel/sourcetrailpythonindexer/branch/master)


## Requirements
* [jedi](https://github.com/davidhalter/jedi) (v0.13.1)
* [SourcetrailDB](https://github.com/CoatiSoftware/SourcetrailDB) for Python (v1)


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
