import shallow_indexer
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

	def test_indexer_records_usage_of_variable_with_multiple_definitions_as_single_local_symbols(self):
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


	def test_indexer_records_usage_of_function_parameter_as_local_symbol(self):
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


	def test_indexer_records_usage_of_function_scope_variable_as_local_symbol(self):
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


# Utility Functions

	def indexSourceCode(self, sourceCode, sysPath = None, verbose = False):
		workingDirectory = os.getcwd()
		astVisitorClient = TestAstVisitorClient()

		shallow_indexer.indexSourceCode(
			sourceCode,
			workingDirectory,
			astVisitorClient,
			verbose,
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
		referencedSymbolId = self.recordSymbol(shallow_indexer.getNameHierarchyForUnsolvedSymbol())
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
