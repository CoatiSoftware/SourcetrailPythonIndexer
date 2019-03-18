import indexer
import multiprocessing
import os
import sourcetraildb as srctrl

import unittest


class TestPythonIndexer(unittest.TestCase):

# Test Recording Symbols

	def test_indexer_records_module_for_source_file(self):
		client = self.indexSourceCode(
			'\n'
		)
		self.assertTrue('MODULE: virtual_file' in client.symbols)


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

	def test_indexer_records_usage_of_variable_with_multiple_definitions_as_multiple_global_symbols(self):
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
		self.assertTrue('virtual_file.py<3:3> at [6:9|6:11]' in client.localSymbols)
		self.assertTrue('virtual_file.py<5:3> at [6:9|6:11]' in client.localSymbols)


	def test_indexer_records_global_variable_as_local_symbol(self):
		client = self.indexSourceCode(
			'foo = 9:\n'
		)
		self.assertTrue('virtual_file.py<1:1> at [1:1|1:3]' in client.localSymbols)


	def test_indexer_records_function_parameter_as_local_symbol(self):
		client = self.indexSourceCode(
			'def foo(bar):\n'
			'	pass\n'
		)
		self.assertTrue('virtual_file.py<1:9> at [1:9|1:11]' in client.localSymbols)


	def test_indexer_records_usage_of_function_parameter_as_local_symbol(self):
		client = self.indexSourceCode(
			'def foo(bar):\n'
			'	x = bar\n'
		)
		self.assertTrue('virtual_file.py<1:9> at [2:6|2:8]' in client.localSymbols)


	def test_indexer_records_function_scope_variable_as_local_symbol(self):
		client = self.indexSourceCode(
			'def foo():\n'
			'	x = 5\n'
		)
		self.assertTrue('virtual_file.py<2:2> at [2:2|2:2]' in client.localSymbols)


	def test_indexer_records_usage_of_variable_as_local_symbol(self):
		client = self.indexSourceCode(
			'def foo():\n'
			'	x = 5\n'
			'	y = x\n'
		)
		self.assertTrue('virtual_file.py<2:2> at [3:6|3:6]' in client.localSymbols)


	def test_indexer_records_method_scope_variable_as_local_symbol(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def bar(self):\n'
			'		baz = 6\n'
		)
		self.assertTrue('virtual_file.py<3:3> at [3:3|3:5]' in client.localSymbols)


# Test Recording References

	def test_indexer_records_import_of_builtin_module(self):
		client = self.indexSourceCode(
			'import itertools\n'
		)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:8|1:16]' in client.references)


	def test_indexer_records_import_of_custom_module(self):
		client = self.indexSourceCode(
			'import re\n'
		)
		self.assertTrue('IMPORT: virtual_file -> re at [1:8|1:9]' in client.references)


	def test_indexer_records_import_of_multiple_modules_with_single_import_statement(self):
		client = self.indexSourceCode(
			'import itertools, re\n'
		)
		self.assertTrue('IMPORT: virtual_file -> itertools at [1:8|1:16]' in client.references)
		self.assertTrue('IMPORT: virtual_file -> re at [1:19|1:20]' in client.references)


	def test_indexer_records_single_class_inheritence(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	pass\n'
			'class Bar(Foo):\n'
			'	pass\n'
		)
		self.assertTrue('INHERITANCE: virtual_file.Bar -> virtual_file.Foo at [3:11|3:13]' in client.references)


	def test_indexer_records_multiple_class_inheritence(self):
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


	def test_indexer_records_class_instantiation(self):
		client = self.indexSourceCode(
			'class Bar:\n'
			'	pass\n'
			'\n'
			'bar = Bar()\n'
		)
		self.assertTrue('TYPE_USAGE: virtual_file -> virtual_file.Bar at [4:7|4:9]' in client.references)


	def test_indexer_records_usage_of_builtin_class(self):
		client = self.indexSourceCode(
			'foo = str(b"bar")\n'
		)
		self.assertTrue('TYPE_USAGE: virtual_file -> builtins.str at [1:7|1:9]' in client.references)


	def test_indexer_records_call_to_builtin_function(self):
		client = self.indexSourceCode(
			'foo = "test string".islower()\n'
		)
		self.assertTrue('CALL: virtual_file -> builtins.str.islower at [1:21|1:27]' in client.references)


	def test_indexer_records_function_call(self):
		client = self.indexSourceCode(
			'def main():\n'
			'	pass\n'
			'\n'
			'main()\n'
		)
		self.assertTrue('CALL: virtual_file -> virtual_file.main at [4:1|4:4]' in client.references)


	def test_indexer_does_not_record_static_field_initialization_as_usage(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	x = 0\n'
		)
		for reference in client.references:
			self.assertFalse(reference.startswith('USAGE: virtual_file.Foo -> virtual_file.Foo.x'))


	def test_indexer_records_usage_of_static_field_via_self(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	x = 0\n'
			'	def bar(self):\n'
			'		y = self.x\n'
		)
		self.assertTrue('USAGE: virtual_file.Foo.bar -> virtual_file.Foo.x at [4:12|4:12]' in client.references)


	def test_indexer_records_initialization_of_non_static_field_via_self_as_usage(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def bar(self):\n'
			'		self.x = None\n'
		)
		self.assertTrue('USAGE: virtual_file.Foo.bar -> virtual_file.Foo.x at [3:8|3:8]' in client.references)


# Test Atomic Ranges

	def test_indexer_records_atomic_range_for_multi_line_string(self):
		client = self.indexSourceCode(
			'foo = """\n'
			'\n'
			'"""\n'
		)
		self.assertTrue('ATOMIC SOURCE RANGE: [1:7|3:3]' in client.atomicSourceRanges)


# Test Recording Errors

	def test_indexer_records_error(self):
		client = self.indexSourceCode(
			'def foo()\n' # missing ':' character
			'	pass\n'
		)
		self.assertTrue('ERROR: "Unexpected token of type "INDENT" encountered." at [2:2|2:1]' in client.errors)


# Test GitHub Issues

	def test_issue_6(self):
		client = self.indexSourceCode(
			'class Foo:\n'
			'	def __init__(self, bar):\n'
			'		self.baz = bar\n'
		)
		self.assertTrue('FIELD: virtual_file.Foo.baz at [3:8|3:10]' in client.symbols)


# Utility Functions

	def indexSourceCode(self, sourceCode, verbose = False):
		workingDirectory = os.getcwd()
		astVisitorClient = TestAstVisitorClient()

		indexer.indexSourceCode(
			sourceCode,
			workingDirectory,
			astVisitorClient,
			verbose
		)

		astVisitorClient.updateReadableOutput()
		return astVisitorClient


class TestAstVisitorClient():

	def __init__(self):
		self.symbols = []
		self.localSymbols = []
		self.references = []
		self.atomicSourceRanges = []
		self.errors = []

		self.serializedSymbolsToIds = {}
		self.symbolIdsToData = {}
		self.serializedLocalSymbolsToIds = {}
		self.localSymbolIdsToData = {}
		self.serializedReferencesToIds = {}
		self.referenceIdsToData = {}

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
			referenceString = ''

			if 'reference_kind' in self.referenceIdsToData[key]:
				referenceString += self.referenceIdsToData[key]['reference_kind'] + ': '
			else:
				referenceString += 'REFERENCE: '

			if 'context_symbol_id' in self.referenceIdsToData[key] and self.referenceIdsToData[key]['context_symbol_id'] in self.symbolIdsToData:
				referenceString += self.symbolIdsToData[self.referenceIdsToData[key]['context_symbol_id']]['name']
			else:
				referenceString += 'UNKNOWN SYMBOL'

			referenceString += ' -> '

			if 'referenced_symbol_id' in self.referenceIdsToData[key] and self.referenceIdsToData[key]['referenced_symbol_id'] in self.symbolIdsToData:
				referenceString += self.symbolIdsToData[self.referenceIdsToData[key]['referenced_symbol_id']]['name']
			else:
				referenceString += 'UNKNOWN SYMBOL'

			if 'reference_location' in self.referenceIdsToData[key]:
				referenceString += ' at ' + self.referenceIdsToData[key]['reference_location']

			referenceString = referenceString.strip()

			if referenceString:
				self.references.append(referenceString)


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
			'reference_kind': referenceKindToString(referenceKind)
		}
		return referenceId


	def recordReferenceLocation(self, referenceId, sourceRange):
		if referenceId in self.referenceIdsToData:
			self.referenceIdsToData[referenceId]['reference_location'] = sourceRange.toString()


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
    unittest.main(exit=False)
