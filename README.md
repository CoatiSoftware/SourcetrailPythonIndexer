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


## Sourcetrail Integration
To run the python indexer from within your Sourcetrail installation, follow these steps:
* make sure that you are running Sourcetrail 2018.4.45 or a later version
* add a new "Custom Command Source Group" to a new or to an existing project
* paste the following string into the source group's "Custom Command" field: `python <path/to>/run.py --source-file-path=%{SOURCE_FILE_PATH} --database-file-path=%{DATABASE_FILE_PATH}`
* replace `<path/to>` with the path where you checked out the SourcetrailPythonIndexer repository
* add your Python files (or the folders that contain those files) to the "Files & Directories to Index" list
* add a ".py" entry to the "Source File Extensions" list (including the dot)
* confirm the settings and start the indexing process


## Executing the Tests
To run the tests for this project, execute the command:
```
$ python test.py
```
