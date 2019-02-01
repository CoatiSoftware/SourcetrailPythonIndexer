# SourcetrailPythonIndexer
Python Indexer for [Sourcetrail](https://www.sourcetrail.com/) based on [jedi](https://github.com/davidhalter/jedi), [parso](https://github.com/davidhalter/parso) and [SourcetrailDB](https://github.com/CoatiSoftware/SourcetrailDB)


## CI Pipelines
Windows: [![Build status](https://ci.appveyor.com/api/projects/status/4vo082swmhmny1a1/branch/master?svg=true)](https://ci.appveyor.com/project/mlangkabel/sourcetrailpythonindexer/branch/master)


## Description
The SourcetrailPythonIndexer project is a Sourcetrail language extension that brings Python support to Sourcetrail. This project is still in a prototype state, but you can already run it on your Python code!

!["find field references"](images/readme/field_references.png "find field references")


## Requirements
* [Python 3](https://www.python.org)
* [jedi 0.13.2](https://pypi.org/project/jedi/0.13.2)
* [parso 0.3.1](https://pypi.org/project/parso/0.3.1)
* [SourcetrailDB](https://github.com/CoatiSoftware/SourcetrailDB) Python bindings


## Setup
* Check out this repository
* Install jedi by running `pip install jedi`
* Download the SourcetrailDB Python bindings for your specific Python version [here](https://github.com/CoatiSoftware/SourcetrailDB/releases) and extract both the `_sourcetraildb.pyd` (`_sourcetraildb.so` on unix) and the `sourcetraildb.py` files to the root of the checked out repository


## Running the Source Code
To index an arbitrary Python source file, execute the command:

```
$ python run.py --source-file-path=path/to/your/python/file.py --database-file-path=path/to/output/database/file.srctrldb
```

This will index the source file and store the data to the provided database filepath. If the database does not exist, an empty database will be created.

You can access an overview that lists all available command line parameters by providing the `-h` argument, which will print the following output to your console:
```
$ python run.py -h
usage: run.py [-h] --database-file-path DATABASE_FILE_PATH --source-file-path
              SOURCE_FILE_PATH [--clear] [--verbose]

Index a Python source file and store the indexed data to a Sourcetrail
database file.

optional arguments:
  -h, --help            show this help message and exit
  --database-file-path DATABASE_FILE_PATH
                        path to the generated Sourcetrail database file
  --source-file-path SOURCE_FILE_PATH
                        path to the source file to index
  --clear               clear the database before indexing
  --verbose             enable verbose console output
```


## Contributing
If you like this project and want to get involved, there are lots of ways you can help:

* __Spread the word.__ The more people want this project to grow, the greater the motivation for the developers to get things done.
* __Test the indexer.__ Run it on your own source code. There are still things that are not handled at all or edge cases that have not been considered yet. If you find anything, just create an issue here. Best, include some sample code snippet that illustrates the issue, so we can use it as a basis to craft a test case for our continuous integration and no one will ever break that case again.
* __Write some code.__ Don't be shy here. You can implement whole new features or fix some bugs, but you can also do some refactoring if you think that it benefits the readability or the maintainability of the code. Still, no matter if you just want to work on cosmetics or implement new features, it would be best if you create an issue here on the issue tracker before you actually start handing in pull requests, so that we can discuss those changes first and thus raise the probability that those changes will get pulled quickly.

To create a pull request, follow these steps:
* Fork the Repo on GitHub.
* Make your commits.
* If you added functionality or fixed a bug, please add a test.
* Add your name to the "Code Contributors" section in AUTHORS.txt file.
* Push to your fork and submit a pull request.


## Executing the Tests
To run the tests for this project, execute the command:
```
$ python test.py
```


## Sourcetrail Integration
To run the python indexer from within your Sourcetrail installation, follow these steps:
* make sure that you are running Sourcetrail 2018.4.45 or a later version
* add a new "Custom Command Source Group" to a new or to an existing Sourcetrail project
* paste the following string into the source group's "Custom Command" field: `python <path/to>/run.py --source-file-path=%{SOURCE_FILE_PATH} --database-file-path=%{DATABASE_FILE_PATH}`
* replace `<path/to>` with the path where you checked out the SourcetrailPythonIndexer repository
* add your Python files (or the folders that contain those files) to the "Files & Directories to Index" list
* add a ".py" entry to the "Source File Extensions" list (including the dot)
* confirm the settings and start the indexing process

!["pick custom sourcegroup"](images/readme/pick_custom_sourcegroup.png "pick custom sourcegroup")!["fill custom sourcegroup"](images/readme/fill_custom_sourcegroup.png "fill custom sourcegroup")


## Features

!["view class members"](images/readme/class_members.png "view class members")

View a class' internal structure to find out which member functions and variables are available and where they are defined.

<br />

!["find field references"](images/readme/field_references.png "find field references")

Find out where a member variable is actually coming from and where it is accessed.

<br />

!["inspect function calls"](images/readme/function_calls.png "inspect function calls")

Inspect call sites of functions all accross the code base.

<br />

!["view local variable usages"](images/readme/local_symbols.png "view local variable usages")

View the definitions of local variables and their usages (note that the definition of `bar` in the `else` branch is not highlighted).
