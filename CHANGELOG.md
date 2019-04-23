# Changelog


## v1.db23.p4

**2019-04-23**

* Added support for Python 2
* Implemented recording "unsolved symbol" when an exception occurred during name resolution of a symbol
* Implemented resolving usages of "super()"
* Implemented recording errors if imported symbol has not been found
* Merged multiple definitions of a local symbol
* Fixed some name hierarchy related issues


## v1.db23.p3

**2019-04-02**

* Implemented recording global variables
* Implemented recording source locations for import statements (issue #4)
* Implemented recording usages of module names within the sourcecode
* Implemented indexer to prepend package names when solving names of symbols
* Implemented recording qualifier locations that can be clicked within Sourcetrail but won't show up if the qualifying symbol is activated
* Implemented recording "unsolved symbol" nodes if the indexer has not been able to deriva a symbol's definition or name
* Changed handling of local variable definitions so that now a single symbol for all (re-)definitions of the same variable within a scope is recorded
* Improved AST logging in "--verbose" mode by printing value and location of visited nodes
* Improved logging by always prepending severity information
* Changed the CLI by adding an optional "--environment-directory-path" parameter that allows to set the python environment used for resolving dependencies within the indexed code
* Changed the CLI by allowing relative paths for the "--source-file-path" and "--database-file-path" parameters
* Added compatibility check to verify if the currently used version of SourcetrailDB supports everything currently used by SourcetrailPythonIndexer (issue #8)
* Fixed CI pipeline did not fail if tests fail


## v1.db23.p2

**2019-02-26**

* Added license info to release packages.
* Implemented recording of references (e.g. calls, usages) of built-in functions and classes.
* Multi-line strings will now be recorded as atomic source ranges, which prevents Sourcetrail from splitting them up in the snippet view.


## v1.db23.p1

**2019-02-18**

* Added downloadable all-in-one release packages for Mac and Linux. The Windows release did not change.


## v1.db23.p0

**2019-02-12**

* First official release of the SourcetrailDB project.
