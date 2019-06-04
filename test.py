import indexer
import multiprocessing
import os
import sourcetraildb as srctrl
import sys
import unittest


class TestPythonIndexer(unittest.TestCase):

# Test Recording Symbols

	def test_indexer_records_module_for_source_file(self):
		client = self.indexSourceCode(
			'\n'
		)
		self.assertTrue('MODULE: virtual_file' in client.symbols)


	def test_indexer_records_module_scope_variable_as_global_variable(self):
		client = self.indexSourceCode(
			'foo = 9:\n'
		)
		self.assertTrue('GLOBAL_VARIABLE: virtual_file.foo at [1:1|1:3]' in client.symbols)


	def test_indexer_records_function_definition(self):
		client = self.indexSourceCode(
			'def foo():\n'
			'	pass\n'
		)
		self.assertTrue('FUNCTION: virtual_file.foo at [1:5|1:7] with scope [1:1|3:0]' in client.symbols)


	def test_indexer_records_class_definition(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	pass\n'
		)
		self.assertTrue('CLASS: virtual_file.Foo at [1:7|1:9] with scope [1:1|3:0]' in client.symbols)


	def test_indexer_records_member_function_definition(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def bar(self):\n'
			'		pass\n'
		)
		self.assertTrue('FUNCTION: virtual_file.Foo.bar at [2:6|2:8] with scope [2:2|4:0]' in client.symbols)


	def test_indexer_records_static_field_definition(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	bar = None\n'
		)
		self.assertTrue('FIELD: virtual_file.Foo.bar at [2:2|2:4]' in client.symbols)


	def test_indexer_records_non_static_field_definition(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def bar(self):\n'
			'		self.x = None\n'
		)
		self.assertTrue('FIELD: virtual_file.Foo.x at [3:8|3:8]' in client.symbols)


# Test Recording Local Symbols

	def test_indexer_records_usage_of_variable_with_multiple_definitions_as_single_local_symbols(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'def foo(bar):\n'
			'	if bar:\n'
			'		baz = 9\n'
			'	else:\n'
			'		baz = 3\n'
			'	return baz\n'
			'foo(True)\n'
			'foo(False)\n'
		)
		self.assertTrue('virtual_file.foo<baz> at [6:9|6:11]' in client.localSymbols)
		self.assertTrue('virtual_file.foo<baz> at [6:9|6:11]' in client.localSymbols)


	def test_indexer_records_function_parameter_as_local_symbol(self):
		client = self.indexSourceCode(
			'def foo(bar):\n'
			'	pass\n'
		)
		self.assertTrue('virtual_file.foo<bar> at [1:9|1:11]' in client.localSymbols)


	def test_indexer_records_usage_of_function_parameter_as_local_symbol(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'def foo(bar):\n'
			'	x = bar\n'
		)
		self.assertTrue('virtual_file.foo<bar> at [2:6|2:8]' in client.localSymbols)


	def test_indexer_records_function_scope_variable_as_local_symbol(self):
		client = self.indexSourceCode(
			'def foo():\n'
			'	x = 5\n'
		)
		self.assertTrue('virtual_file.foo<x> at [2:2|2:2]' in client.localSymbols)


	def test_indexer_records_usage_of_function_scope_variable_as_local_symbol(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'def foo():\n'
			'	x = 5\n'
			'	y = x\n'
		)
		self.assertTrue('virtual_file.foo<x> at [3:6|3:6]' in client.localSymbols)


	def test_indexer_records_method_scope_variable_as_local_symbol(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def bar(self):\n'
			'		baz = 6\n'
		)
		self.assertTrue('virtual_file.Foo.bar<baz> at [3:3|3:5]' in client.localSymbols)


# Test Recording References

	def test_indexer_records_import_of_builtin_module(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import itertools\n'
		)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:8|1:16]' in client.references)


	def test_indexer_records_import_of_custom_module(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import re\n'
		)
		self.assertTrue('IMPORT: virtual_file -> re at [1:8|1:9]' in client.references)


	def test_indexer_records_import_of_multiple_modules_with_single_import_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import itertools, re\n'
		)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:8|1:16]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re at [1:19|1:20]' in client.references)


	def test_indexer_records_import_of_aliased_module(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import itertools as it\n'
		)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:8|1:16]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:21|1:22]' in client.references)


	def test_indexer_records_import_of_multiple_alised_modules_with_single_import_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import itertools as it, re as regex\n'
		)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:8|1:16]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:21|1:22]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re at [1:25|1:26]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re at [1:31|1:35]' in client.references)


	def test_indexer_records_import_of_function(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from re import match\n'
		)
		self.assertTrue('USAGE: virtual_file -> re at [1:6|1:7]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.match at [1:16|1:20]' in client.references)


	def test_indexer_records_import_of_aliased_function(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from re import match as m\n'
		)
		self.assertTrue('USAGE: virtual_file -> re at [1:6|1:7]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.match at [1:16|1:20]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.match at [1:25|1:25]' in client.references)


	def test_indexer_records_import_of_multiple_aliased_functions_with_single_import_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from re import match as m, escape as e\n'
		)
		self.assertTrue('USAGE: virtual_file -> re at [1:6|1:7]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.match at [1:16|1:20]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.match at [1:25|1:25]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.escape at [1:28|1:33]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.escape at [1:38|1:38]' in client.references)


	def test_indexer_records_import_of_variable(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from sys import float_info\n'
		)
		self.assertTrue('USAGE: virtual_file -> sys at [1:6|1:8]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.float_info at [1:17|1:26]' in client.references)


	def test_indexer_records_import_of_aliased_variable(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from sys import float_info as FI\n'
		)
		self.assertTrue('USAGE: virtual_file -> sys at [1:6|1:8]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.float_info at [1:17|1:26]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.float_info at [1:31|1:32]' in client.references)


	def test_indexer_records_import_of_multiple_aliased_variables_with_single_import_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from sys import float_info as FI, api_version as AI\n'
		)
		self.assertTrue('USAGE: virtual_file -> sys at [1:6|1:8]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.float_info at [1:17|1:26]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.float_info at [1:31|1:32]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.api_version at [1:35|1:45]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> sys.api_version at [1:50|1:51]' in client.references)


	def test_indexer_records_import_of_class(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from re import Scanner\n'
		)
		self.assertTrue('USAGE: virtual_file -> re at [1:6|1:7]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:16|1:22]' in client.references)


	def test_indexer_records_import_of_aliased_class(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from re import Scanner as Sc\n'
		)
		self.assertTrue('USAGE: virtual_file -> re at [1:6|1:7]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:16|1:22]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:27|1:28]' in client.references)


	def test_indexer_records_import_of_multiple_aliased_classes_with_single_import_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'from re import Scanner as S1, Scanner as S2\n'
		)
		self.assertTrue('USAGE: virtual_file -> re at [1:6|1:7]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:16|1:22]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:27|1:28]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:31|1:37]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re.Scanner at [1:42|1:43]' in client.references)


	def test_indexer_records_usage_of_imported_module(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import sys\n'
			'dir(sys)\n'
		)
		self.assertTrue('USAGE: virtual_file -> sys at [2:5|2:7]' in client.references)


	def test_indexer_records_single_class_inheritence(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo:\n'
			'	pass\n'
			'class Bar(Foo):\n'
			'	pass\n'
		)
		self.assertTrue('INHERITANCE: virtual_file.Bar -> virtual_file.Foo at [3:11|3:13]' in client.references)


	def test_indexer_records_multiple_class_inheritence(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo:\n'
			'	pass\n'
			'class Bar():\n'
			'	pass\n'
			'class Baz(Foo, Bar):\n'
			'	pass\n'
		)
		self.assertTrue('INHERITANCE: virtual_file.Baz -> virtual_file.Foo at [5:11|5:13]' in client.references)
		self.assertTrue('INHERITANCE: virtual_file.Baz -> virtual_file.Bar at [5:16|5:18]' in client.references)


	def test_indexer_records_instantiation_of_custom_class(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Bar:\n'
			'	pass\n'
			'\n'
			'bar = Bar()\n'
		)
		self.assertTrue('TYPE_USAGE: virtual_file -> virtual_file.Bar at [4:7|4:9]' in client.references)


	def test_indexer_records_instantiation_of_environment_class(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import itertools\n'
			'itertools.cycle(None)\n'
		)
		self.assertTrue('CALL: virtual_file -> itertools.cycle at [2:11|2:15]' in client.references)


	def test_indexer_records_usage_of_super_keyword(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo(object):\n'
			'	def foo():\n'
			'		pass\n'
			'\n'
			'class Bar(Foo):\n'
			'	def bar(self):\n'
			'		super().foo()\n'
		)
		self.assertTrue(
			'TYPE_USAGE: virtual_file.Bar.bar -> builtins.super at [7:3|7:7]' in client.references or
			'CALL: virtual_file.Bar.bar -> builtins.super at [7:3|7:7]' in client.references) # somehow the CI records a "call" reference. maybe that's a python 2 thing...


	def test_indexer_records_usage_of_builtin_class(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'foo = str(b"bar")\n'
		)
		self.assertTrue('TYPE_USAGE: virtual_file -> builtins.str at [1:7|1:9]' in client.references)


	def test_indexer_records_call_to_builtin_function(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'foo = "test string".islower()\n'
		)
		self.assertTrue('CALL: virtual_file -> builtins.str.islower at [1:21|1:27]' in client.references)

#	def test_indexer_records_call_to_environment_function(self):
#		client = self.indexSourceCode(
#			'import sys\n'
#			'sys.callstats()\n'
#		)
#		self.assertTrue('CALL: virtual_file -> sys.callstats at [2:5|2:13]' in client.references)


	def test_indexer_records_function_call(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'def main():\n'
			'	pass\n'
			'\n'
			'main()\n'
		)
		self.assertTrue('CALL: virtual_file -> virtual_file.main at [4:1|4:4]' in client.references)


	def test_indexer_does_not_record_static_field_initialization_as_usage(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo:\n'
			'	x = 0\n'
		)
		for reference in client.references:
			self.assertFalse(reference.startswith('USAGE: virtual_file.Foo -> virtual_file.Foo.x'))


	def test_indexer_records_usage_of_static_field_via_self(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo:\n'
			'	x = 0\n'
			'	def bar(self):\n'
			'		y = self.x\n'
		)
		self.assertTrue('USAGE: virtual_file.Foo.bar -> virtual_file.Foo.x at [4:12|4:12]' in client.references)


	def test_indexer_records_initialization_of_non_static_field_via_self_as_usage(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def bar(self):\n'
			'		self.x = None\n'
		)
		self.assertTrue('USAGE: virtual_file.Foo.bar -> virtual_file.Foo.x at [3:8|3:8]' in client.references)


# Test Qualifiers

	def test_indexer_records_module_as_qualifier_in_import_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import pkg.mod\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertTrue('pkg at [1:8|1:10]' in client.qualifiers)


	def test_indexer_records_module_as_qualifier_in_expression_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import sys\n'
			'print(sys.executable)\n'
		)
		self.assertTrue('sys at [2:7|2:9]' in client.qualifiers)


	def test_indexer_records_class_as_qualifier_in_expression_statement(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'class Foo:\n'
			'	bar = 0\n'
			'baz = Foo.bar\n'
		)
		self.assertTrue('virtual_file.Foo at [3:7|3:9]' in client.qualifiers)

# Test Package and Module Names

	def test_indexer_resolves_packge_name_relative_to_sys_path(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import pkg\n'
			'c = pkg.PackageLevelClass()\n'
			'print(c.field)\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertTrue('NON-INDEXED MODULE: pkg' in client.symbols)
		self.assertTrue('NON-INDEXED CLASS: pkg.PackageLevelClass' in client.symbols)
		self.assertTrue('NON-INDEXED SYMBOL: pkg.PackageLevelClass.field' in client.symbols)


	def test_indexer_resolves_module_name_relative_to_sys_path(self): #FixmeInShallowMode
		client = self.indexSourceCode(
			'import pkg.mod\n'
			'c = pkg.mod.ModuleLevelClass()\n'
			'print(c.field)\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertTrue('NON-INDEXED MODULE: pkg.mod' in client.symbols)
		self.assertTrue('NON-INDEXED CLASS: pkg.mod.ModuleLevelClass' in client.symbols)
		self.assertTrue('NON-INDEXED SYMBOL: pkg.mod.ModuleLevelClass.field' in client.symbols)


# Test Atomic Ranges

	def test_indexer_records_atomic_range_for_multi_line_string(self):
		client = self.indexSourceCode(
			'foo = """\n'
			'\n'
			'"""\n'
		)
		self.assertTrue('ATOMIC SOURCE RANGE: [1:7|3:3]' in client.atomicSourceRanges)


# Test Recording Errors

	def test_indexer_records_syntax_error(self):
		client = self.indexSourceCode(
			'def foo()\n' # missing ':' character
			'	pass\n'
		)
		self.assertTrue('ERROR: "Unexpected token of type "INDENT" encountered." at [2:2|2:1]' in client.errors)


	def test_indexer_records_error_if_imported_package_has_not_been_found(self):
		client = self.indexSourceCode(
			'import this_is_not_a_real_package\n'
		)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:8|1:33]' in client.errors)


	def test_indexer_records_error_if_package_of_imported_module_has_not_been_found(self):
		client = self.indexSourceCode(
			'import this_is_not_a_real_package.this_is_not_a_real_module\n'
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:8|1:33]' in client.errors)


	def test_indexer_records_error_if_imported_module_has_not_been_found(self):
		client = self.indexSourceCode(
			'import pkg.this_is_not_a_real_module\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_module" has not been found." at [1:12|1:36]' in client.errors)


	def test_indexer_records_error_for_each_unsolved_import_in_single_import_statement(self):
		client = self.indexSourceCode(
			'import this_is_not_a_real_package, this_is_not_a_real_package.this_is_not_a_real_module, pkg.this_is_not_a_real_module\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertEqual(len(client.errors), 3)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:8|1:33]' in client.errors)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:36|1:61]' in client.errors)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_module" has not been found." at [1:94|1:118]' in client.errors)


	def test_indexer_records_error_if_imported_aliased_package_has_not_been_found(self):
		client = self.indexSourceCode(
			'import this_is_not_a_real_package as p\n'
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:8|1:33]' in client.errors)


	def test_indexer_records_error_if_package_of_imported_aliased_module_has_not_been_found(self):
		client = self.indexSourceCode(
			'import this_is_not_a_real_package.this_is_not_a_real_module as mod\n'
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:8|1:33]' in client.errors)


	def test_indexer_records_error_if_imported_aliased_module_has_not_been_found(self):
		client = self.indexSourceCode(
			'import pkg.this_is_not_a_real_module as mod\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_module" has not been found." at [1:12|1:36]' in client.errors)


	def test_indexer_records_error_for_each_unsolved_aliased_import_in_single_import_statement(self):
		client = self.indexSourceCode(
			'import this_is_not_a_real_package as p, this_is_not_a_real_package.this_is_not_a_real_module as mod1, pkg.this_is_not_a_real_module as mod2\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertEqual(len(client.errors), 3)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:8|1:33]' in client.errors)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:41|1:66]' in client.errors)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_module" has not been found." at [1:107|1:131]' in client.errors)


	def test_indexer_records_error_if_package_of_imported_aliased_symbol_has_not_been_found(self):
		client = self.indexSourceCode(
			'from this_is_not_a_real_package import this_is_not_a_real_symbol as sym\n'
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:6|1:31]' in client.errors)


	def test_indexer_records_error_if_package_of_module_of_imported_aliased_symbol_has_not_been_found(self):
		client = self.indexSourceCode(
			'from this_is_not_a_real_package.this_is_not_a_real_module import this_is_not_a_real_symbol as sym\n'
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_package" has not been found." at [1:6|1:31]' in client.errors)


	def test_indexer_records_error_if_module_of_imported_aliased_symbol_has_not_been_found(self):
		client = self.indexSourceCode(
			'from pkg.this_is_not_a_real_module import this_is_not_a_real_symbol as sym\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertEqual(len(client.errors), 1)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_module" has not been found." at [1:10|1:34]' in client.errors)


	def test_indexer_records_error_if_imported_aliased_symbol_has_not_been_found(self):
		client = self.indexSourceCode(
			'from pkg import this_is_not_a_real_symbol_1 as sym1, this_is_not_a_real_symbol_2 as sym2\n',
			None,
			[os.path.join(os.getcwd(), 'data', 'test')]
		)
		self.assertEqual(len(client.errors), 2)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_symbol_1" has not been found." at [1:17|1:43]' in client.errors)
		self.assertTrue('ERROR: "Imported symbol named "this_is_not_a_real_symbol_2" has not been found." at [1:54|1:80]' in client.errors)


# Test GitHub Issues

	def test_issue_6(self): # Member variable has wrong name qualifiers if initialized from function parameter
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def __init__(self, bar):\n'
			'		self.baz = bar\n'
		)
		self.assertTrue('FIELD: virtual_file.Foo.baz at [3:8|3:10]' in client.symbols)


	def test_issue_8(self): # Check if compatible to used SourcetrailDB build
		self.assertTrue(indexer.isSourcetrailDBVersionCompatible())


	def test_issue_26_1(self): # For-Loop-Iterator not recorded as local symbol
		client = self.indexSourceCode(
			'def foo():\n'
			'	for n in [1, 2, 3]:\n'
			'		print(n)\n'
		)
		self.assertTrue('virtual_file.foo<n> at [2:6|2:6]' in client.localSymbols)
		self.assertTrue('virtual_file.foo<n> at [3:9|3:9]' in client.localSymbols)


	def test_issue_26_2(self): # For-Loop-Iterator not recorded as global symbol
		client = self.indexSourceCode(
			'for n in [1, 2, 3]:\n'
			'	print(n)\n'
		)
		self.assertTrue('GLOBAL_VARIABLE: virtual_file.n at [1:5|1:5]' in client.symbols)
		self.assertTrue('USAGE: virtual_file -> virtual_file.n at [2:8|2:8]' in client.references)


	def test_issue_27(self): # Boolean value "True" is recorded as "non-indexed global variable"
		client = self.indexSourceCode(
			'class Test():\n'
			'	def foo(self, bar=True):\n'
			'		pass\n'
		)
		self.assertEqual(len(client.references), 0)


	def test_issue_28(self): # Default argument of function is "unsolved" if it has the same name as the function
		client = self.indexSourceCode(
			'foo = 9\n'
			'def foo(baz=foo):\n'
			'	pass\n'
		)
		self.assertTrue('USAGE: virtual_file.foo -> virtual_file.foo at [2:13|2:15]' in client.references)


	def test_issue_29(self): # Local symbol not solved correctly if defined in parent scope function
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def __init__(self):\n'
			'		def bar():\n'
			'			self.foo = 79\n'
		)
		self.assertTrue('virtual_file.Foo.__init__<self> at [2:15|2:18]' in client.localSymbols)
		self.assertTrue('virtual_file.Foo.__init__<self> at [4:4|4:7]' in client.localSymbols)


	def test_issue_30(self): # Unable to solve method calls for multiple inheritence if "super()" is used
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def foo(self):\n'
			'		pass\n'
			'\n'
			'class Bar:\n'
			'	def bar(self):\n'
			'		pass\n'
			'\n'
			'class Baz(Foo, Bar):\n'
			'	def baz(self):\n'
			'		super().foo()\n'
			'		super().bar()\n'
		)
		self.assertTrue('CALL: virtual_file.Baz.baz -> virtual_file.Foo.foo at [11:11|11:13]' in client.references)
		self.assertTrue('CALL: virtual_file.Baz.baz -> virtual_file.Bar.bar at [12:11|12:13]' in client.references)


	def test_issue_34(self): # Context of method that is defined inside a for loop is not solved correctly
		client = self.indexSourceCode(
			'def foo():\n'
			'	for bar in []:\n'
			'		def baz():\n'
			'			pass\n'
		)
		self.assertTrue('FUNCTION: virtual_file.foo.baz at [3:7|3:9] with scope [3:3|5:0]' in client.symbols)


	def test_issue_38(self): # Local symbols in field instantiation are recorded as global variables
		client = self.indexSourceCode(
			'class Foo:\n'
			'	bar = {"a": "b"}\n'
			'	baz = dict((k, v) for k, v in bar.items())\n'
		)
		self.assertTrue('virtual_file.Foo<k> at [3:24|3:24]' in client.localSymbols)
		self.assertTrue('virtual_file.Foo<v> at [3:27|3:27]' in client.localSymbols)


	def test_issue_40(self): # global symbol defined in iterable argument is recorded as child of "unsolved symbol"
		client = self.indexSourceCode(
			'sorted(name[:-3] for name in ["foobar"])\n'
		)
		self.assertTrue('GLOBAL_VARIABLE: virtual_file.name at [1:22|1:25]' in client.symbols)


	def test_issue_41(self): # Indexer fails to record multiple call edges for a single call site
		client = self.indexSourceCode(
			'def foo(bar):\n'
			'	bar.bar()\n'
			'\n'
			'class A:\n'
			'	def bar(self):\n'
			'		print("A")\n'
			'\n'
			'class B:\n'
			'	def bar(self):\n'
			'		print("B")\n'
			'\n'
			'foo(A())\n'
			'foo(B())\n'
		)
		self.assertTrue('CALL: virtual_file.foo -> virtual_file.A.bar at [2:6|2:8]' in client.references)
		self.assertTrue('CALL: virtual_file.foo -> virtual_file.B.bar at [2:6|2:8]' in client.references)


	def test_issue_49(self): # Tracking __init__ constructor
		client = self.indexSourceCode(
			'class Foo:\n'
			'	pass\n'
			'foo = Foo()\n'
		)
		self.assertTrue('CALL: virtual_file -> virtual_file.Foo.__init__ at [3:7|3:9]' in client.references)


# Utility Functions

	def indexSourceCode(self, sourceCode, environmentPath = None, sysPath = None, verbose = False):
		workingDirectory = os.getcwd()
		astVisitorClient = TestAstVisitorClient()

		indexer.indexSourceCode(
			sourceCode,
			workingDirectory,
			astVisitorClient,
			verbose,
			environmentPath,
			sysPath
		)

		astVisitorClient.updateReadableOutput()
		return astVisitorClient


class TestAstVisitorClient():

	def __init__(self):
		self.symbols = []
		self.localSymbols = []
		self.references = []
		self.qualifiers = []
		self.atomicSourceRanges = []
		self.errors = []

		self.serializedSymbolsToIds = {}
		self.symbolIdsToData = {}
		self.serializedLocalSymbolsToIds = {}
		self.localSymbolIdsToData = {}
		self.serializedReferencesToIds = {}
		self.referenceIdsToData = {}
		self.qualifierIdsToData = {}

		self.nextSymbolId = 1


	def updateReadableOutput(self):
		self.symbols = []
		for key in self.symbolIdsToData:
			symbolString = ''

			if 'definition_kind' in self.symbolIdsToData[key]:
				symbolString += self.symbolIdsToData[key]['definition_kind'] + ' '
			else:
				symbolString += 'NON-INDEXED '

			if 'symbol_kind' in self.symbolIdsToData[key]:
				symbolString += self.symbolIdsToData[key]['symbol_kind'] + ': '
			else:
				symbolString += 'SYMBOL: '

			if 'name' in self.symbolIdsToData[key]:
				symbolString += self.symbolIdsToData[key]['name']

			if 'symbol_location' in self.symbolIdsToData[key]:
				symbolString += ' at ' + self.symbolIdsToData[key]['symbol_location']

			if 'scope_location' in self.symbolIdsToData[key]:
				symbolString += ' with scope ' + self.symbolIdsToData[key]['scope_location']

			if 'signature_location' in self.symbolIdsToData[key]:
				symbolString += ' with signature ' + self.symbolIdsToData[key]['signature_location']

			symbolString = symbolString.strip()

			if symbolString:
				self.symbols.append(symbolString)

		self.localSymbols = []
		for key in self.localSymbolIdsToData:
			localSymbolString = ''

			if 'name' in self.localSymbolIdsToData[key]:
				localSymbolString += self.localSymbolIdsToData[key]['name']

			if localSymbolString and 'local_symbol_locations' in self.localSymbolIdsToData[key]:
				for location in self.localSymbolIdsToData[key]['local_symbol_locations']:
					self.localSymbols.append(localSymbolString + ' at ' + location)

		self.references = []
		for key in self.referenceIdsToData:
			if 'reference_location' not in self.referenceIdsToData[key] or len(self.referenceIdsToData[key]['reference_location']) == 0:
				self.referenceIdsToData[key]['reference_location'].append('')

			for referenceLocation in self.referenceIdsToData[key]['reference_location']:
				referenceString = ''

				if 'reference_kind' in self.referenceIdsToData[key]:
					referenceString += self.referenceIdsToData[key]['reference_kind'] + ': '
				else:
					referenceString += 'UNKNOWN REFERENCE: '

				if 'context_symbol_id' in self.referenceIdsToData[key] and self.referenceIdsToData[key]['context_symbol_id'] in self.symbolIdsToData:
					referenceString += self.symbolIdsToData[self.referenceIdsToData[key]['context_symbol_id']]['name']
				else:
					referenceString += 'UNKNOWN SYMBOL'

				referenceString += ' -> '

				if 'referenced_symbol_id' in self.referenceIdsToData[key] and self.referenceIdsToData[key]['referenced_symbol_id'] in self.symbolIdsToData:
					referenceString += self.symbolIdsToData[self.referenceIdsToData[key]['referenced_symbol_id']]['name']
				else:
					referenceString += 'UNKNOWN SYMBOL'

				if referenceLocation:
					referenceString += ' at ' + referenceLocation

				referenceString = referenceString.strip()

				if referenceString:
					self.references.append(referenceString)

		self.qualifiers = []
		for key in self.qualifierIdsToData:
			symbolName = 'UNKNOWN SYMBOL'
			if 'id' in self.qualifierIdsToData[key] and self.qualifierIdsToData[key]['id'] in self.symbolIdsToData:
				symbolName = self.symbolIdsToData[self.qualifierIdsToData[key]['id']]['name']

			for qualifierLocation in self.qualifierIdsToData[key]['qualifier_locations']:
				qualifierString = symbolName

				if qualifierLocation:
					qualifierString += ' at ' + qualifierLocation

				if qualifierString:
					self.qualifiers.append(qualifierString)


	def getNextElementId(self):
		id = self.nextSymbolId
		self.nextSymbolId += 1
		return id


	def recordSymbol(self, nameHierarchy):
		serialized = nameHierarchy.serialize()

		if serialized in self.serializedSymbolsToIds:
			return self.serializedSymbolsToIds[serialized]

		symbolId = self.getNextElementId()
		self.serializedSymbolsToIds[serialized] = symbolId
		self.symbolIdsToData[symbolId] = {
			'id': symbolId,
			'name': nameHierarchy.getDisplayString()
		}
		return symbolId


	def recordSymbolDefinitionKind(self, symbolId, symbolDefinitionKind):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]['definition_kind'] = symbolDefinitionKindToString(symbolDefinitionKind)


	def recordSymbolKind(self, symbolId, symbolKind):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]['symbol_kind'] = symbolKindToString(symbolKind)


	def recordSymbolLocation(self, symbolId, sourceRange):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]['symbol_location'] = sourceRange.toString()


	def recordSymbolScopeLocation(self, symbolId, sourceRange):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]['scope_location'] = sourceRange.toString()


	def recordSymbolSignatureLocation(self, symbolId, sourceRange):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]['signature_location'] = sourceRange.toString()


	def recordReference(self, contextSymbolId, referencedSymbolId, referenceKind):
		serialized = str(contextSymbolId) + ' -> ' + str(referencedSymbolId) + '[' + str(referenceKind) + ']'
		if serialized in self.serializedReferencesToIds:
			return self.serializedReferencesToIds[serialized]

		referenceId = self.getNextElementId()
		self.serializedReferencesToIds[serialized] = referenceId
		self.referenceIdsToData[referenceId] = {
			'id': referenceId,
			'context_symbol_id': contextSymbolId,
			'referenced_symbol_id': referencedSymbolId,
			'reference_kind': referenceKindToString(referenceKind),
			'reference_location': []
		}
		return referenceId


	def recordReferenceLocation(self, referenceId, sourceRange):
		if referenceId in self.referenceIdsToData:
			self.referenceIdsToData[referenceId]['reference_location'].append(sourceRange.toString())


	def recordReferenceIsAmbiuous(self, referenceId):
		raise NotImplementedError


	def recordReferenceToUnsolvedSymhol(self, contextSymbolId, referenceKind, sourceRange):
		referencedSymbolId = self.recordSymbol(indexer.getNameHierarchyForUnsolvedSymbol())
		referenceId = self.recordReference(contextSymbolId, referencedSymbolId, referenceKind)
		self.recordReferenceLocation(referenceId, sourceRange)
		return referenceId


	def recordQualifierLocation(self, referencedSymbolId, sourceRange):
		if referencedSymbolId not in self.qualifierIdsToData:
			self.qualifierIdsToData[referencedSymbolId] = {
				'id': referencedSymbolId,
				'qualifier_locations': []
			}
		self.qualifierIdsToData[referencedSymbolId]['qualifier_locations'].append(sourceRange.toString())


	def recordFile(self, filePath):
		serialized = filePath

		if serialized in self.serializedSymbolsToIds:
			return self.serializedSymbolsToIds[serialized]

		fileId = self.getNextElementId()
		self.serializedSymbolsToIds[serialized] = fileId
		self.symbolIdsToData[fileId] = {
			'id': fileId,
			'name': filePath,
			'symbol_kind': 'FILE',
			'definition_kind': 'INDEXED'
		}
		return fileId


	def recordFileLanguage(self, fileId, languageIdentifier):
		# FIXME: implement this one!
		return


	def recordLocalSymbol(self, name):
		if name in self.serializedLocalSymbolsToIds:
			return self.serializedLocalSymbolsToIds[name]

		localSymbolId = self.getNextElementId()
		self.serializedLocalSymbolsToIds[name] = localSymbolId
		self.localSymbolIdsToData[localSymbolId] = {
			'id': localSymbolId,
			'name': name,
			'local_symbol_locations': []
		}
		return localSymbolId


	def recordLocalSymbolLocation(self, localSymbolId, sourceRange):
		if localSymbolId in self.localSymbolIdsToData:
			self.localSymbolIdsToData[localSymbolId]['local_symbol_locations'].append(sourceRange.toString())


	def recordAtomicSourceRange(self, sourceRange):
		self.atomicSourceRanges.append('ATOMIC SOURCE RANGE: ' + sourceRange.toString())
		return


	def recordError(self, message, fatal, sourceRange):
		errorString = ''
		if fatal:
			errorString += 'FATAL '
		errorString += 'ERROR: "' + message + '" at ' + sourceRange.toString()
		self.errors.append(errorString)
		return


def symbolDefinitionKindToString(symbolDefinitionKind):
	if symbolDefinitionKind == srctrl.SYMBOL_ANNOTATION:
		return 'EXPLICIT'
	if symbolDefinitionKind == srctrl.DEFINITION_IMPLICIT:
		return 'IMPLICIT'
	return ''

def symbolKindToString(symbolKind):
	if symbolKind == srctrl.SYMBOL_TYPE:
		return 'TYPE'
	if symbolKind == srctrl.SYMBOL_BUILTIN_TYPE:
		return 'BUILTIN_TYPE'
	if symbolKind == srctrl.SYMBOL_MODULE:
		return 'MODULE'
	if symbolKind == srctrl.SYMBOL_NAMESPACE:
		return 'NAMESPACE'
	if symbolKind == srctrl.SYMBOL_PACKAGE:
		return 'PACKAGE'
	if symbolKind == srctrl.SYMBOL_STRUCT:
		return 'STRUCT'
	if symbolKind == srctrl.SYMBOL_CLASS:
		return 'CLASS'
	if symbolKind == srctrl.SYMBOL_INTERFACE:
		return 'INTERFACE'
	if symbolKind == srctrl.SYMBOL_ANNOTATION:
		return 'ANNOTATION'
	if symbolKind == srctrl.SYMBOL_GLOBAL_VARIABLE:
		return 'GLOBAL_VARIABLE'
	if symbolKind == srctrl.SYMBOL_FIELD:
		return 'FIELD'
	if symbolKind == srctrl.SYMBOL_FUNCTION:
		return 'FUNCTION'
	if symbolKind == srctrl.SYMBOL_METHOD:
		return 'METHOD'
	if symbolKind == srctrl.SYMBOL_ENUM:
		return 'ENUM'
	if symbolKind == srctrl.SYMBOL_ENUM_CONSTANT:
		return 'ENUM_CONSTANT'
	if symbolKind == srctrl.SYMBOL_TYPEDEF:
		return 'TYPEDEF'
	if symbolKind == srctrl.SYMBOL_TEMPLATE_PARAMETER:
		return 'TEMPLATE_PARAMETER'
	if symbolKind == srctrl.SYMBOL_TYPE_PARAMETER:
		return 'TYPE_PARAMETER'
	if symbolKind == srctrl.SYMBOL_FILE:
		return 'FILE'
	if symbolKind == srctrl.SYMBOL_MACRO:
		return 'MACRO'
	if symbolKind == srctrl.SYMBOL_UNION:
		return 'UNION'
	return ''


def referenceKindToString(referenceKind):
	if referenceKind == srctrl.REFERENCE_TYPE_USAGE:
		return 'TYPE_USAGE'
	if referenceKind == srctrl.REFERENCE_USAGE:
		return 'USAGE'
	if referenceKind == srctrl.REFERENCE_CALL:
		return 'CALL'
	if referenceKind == srctrl.REFERENCE_INHERITANCE:
		return 'INHERITANCE'
	if referenceKind == srctrl.REFERENCE_OVERRIDE:
		return 'OVERRIDE'
	if referenceKind == srctrl.REFERENCE_TEMPLATE_ARGUMENT:
		return 'TEMPLATE_ARGUMENT'
	if referenceKind == srctrl.REFERENCE_TYPE_ARGUMENT:
		return 'TYPE_ARGUMENT'
	if referenceKind == srctrl.REFERENCE_TEMPLATE_DEFAULT_ARGUMENT:
		return 'TEMPLATE_DEFAULT_ARGUMENT'
	if referenceKind == srctrl.REFERENCE_TEMPLATE_SPECIALIZATION:
		return 'TEMPLATE_SPECIALIZATION'
	if referenceKind == srctrl.REFERENCE_TEMPLATE_MEMBER_SPECIALIZATION:
		return 'TEMPLATE_MEMBER_SPECIALIZATION'
	if referenceKind == srctrl.REFERENCE_INCLUDE:
		return 'INCLUDE'
	if referenceKind == srctrl.REFERENCE_IMPORT:
		return 'IMPORT'
	if referenceKind == srctrl.REFERENCE_MACRO_USAGE:
		return 'MACRO_USAGE'
	if referenceKind == srctrl.REFERENCE_ANNOTATION_USAGE:
		return 'ANNOTATION_USAGE'
	return ''


if __name__ == '__main__':
    unittest.main(exit=True)
