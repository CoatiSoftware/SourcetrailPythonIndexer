# Changelog


## v1.db25.p1

**2019-11-26**

* Switched form Apache License to GNU GENERAL PUBLIC LICENSE.
* Allow to use "unsafe" Python environment if this environment has explicitly been specified by the user.


## v1.db25.p0

**2019-11-05**

* Added shallow indexer that is less precide than the normal indexer but much faster. This mode can be invoked by adding the `--shallow` command line argument.


## v1.db24.p2

**2019-08-26**

* Implemented recording a reference to the __init__() method of a class for locations where a class object is initialized (issue #49)
* Fixed issue where some virus scanners had a false positive detection for the SourcetrailPythonIndexer (issue #48)
* Updated to jedi 0.15.0
* Fixed crash when looking up names for some builtin symbols


## v1.db24.p1

**2019-08-06**

* Updated to jedi 0.14.1 and parso 0.5.1 to fix issues #26, #28 and #30
* Fixed opening and reading source files when using Python 2


## v1.db24.p0

**2019-05-28**

* Changed commandline api by moving the current main functionality of indexing a source file to the "index" command
* Added new "check-environment" command that can be used to check whether a given Python environment will be usable by the indexer


## v0.db24.p1

**2019-05-21**

* Added exception handling for accessing jedi definition, so that these exceptions only cause one symbol to be unsolved and the rest of the file will still be indexed
* Switched to reading source code using UTF-8 encoding by default


## v0.db24.p0

**2019-05-20**

* Updated to Sourcetrail database format version 24
* Implemented recording unsolved symbol locations as "unsolved", so they can be displayed as such by Sourcetrail
* Implemented allowing to record multiple references for one source location (e.g. when different code paths result in different functions being called)
* Implemented printing of detailed error if provided python environment is invalid
* Fixed an issue where global symbols defined in iterable argument are recorded as child of "unsolved symbol" (issue #40)


## v0.db23.p4

**2019-04-23**

* Added support for Python 2
* Implemented recording "unsolved symbol" when an exception occurred during name resolution of a symbol
* Implemented resolving usages of "super()"
* Implemented recording errors if imported symbol has not been found
* Merged multiple definitions of a local symbol
* Fixed some name hierarchy related issues


## v0.db23.p3

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


## v0.db23.p2

**2019-02-26**

* Added license info to release packages.
* Implemented recording of references (e.g. calls, usages) of built-in functions and classes.
* Multi-line strings will now be recorded as atomic source ranges, which prevents Sourcetrail from splitting them up in the snippet view.


## v0.db23.p1

**2019-02-18**

* Added downloadable all-in-one release packages for Mac and Linux. The Windows release did not change.


## v0.db23.p0

**2019-02-12**

* First official release of the SourcetrailDB project.
