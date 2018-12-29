import indexer
import multiprocessing
import os
import sourcetraildb as srctrl

import unittest


class TestPythonIndexer(unittest.TestCase):

# Test Recording Symbols

	def test_indexer_records_class_definition(self):
		client = self.indexSourceCode(
			"class Foo:\n"
			"	pass\n"
		)
		self.assertTrue("CLASS: Foo at [1:7|1:9] with scope [1:1|3:0]" in client.symbols)


	def test_indexer_records_field_definition(self):
		client = self.indexSourceCode(
			"class Foo:\n"
			"	bar = None\n"
		)
		self.assertTrue("FIELD: Foo.bar at [2:2|2:4]" in client.symbols)


# Test Recording Local Symbols

	def test_indexer_records_function_parameter_as_local_symbol(self):
		client = self.indexSourceCode(
			"def foo(bar):\n"
			"	pass\n"
		)
		self.assertTrue("virtual_file.py<1:9> at [1:9|1:11]" in client.localSymbols)


# Test Recording References

	def test_indexer_records_class_instantiation(self):
		client = self.indexSourceCode(
			"class Bar:\n"
			"	pass\n"
			"\n"
			"bar = Bar()\n"
		)
		self.assertTrue("TYPE_USAGE: virtual_file.py -> Bar at [4:7|4:9]" in client.references)


	def test_indexer_records_function_call(self):
		client = self.indexSourceCode(
			"def main():\n"
			"	pass\n"
			"\n"
			"main()\n"
		)
		self.assertTrue("CALL: virtual_file.py -> main at [4:1|4:4]" in client.references)


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

	symbols = []
	localSymbols = []
	references = []


	def __init__(self):
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
			symbolString = ""
			
			if "definition_kind" in self.symbolIdsToData[key]:
				symbolString += self.symbolIdsToData[key]["definition_kind"] + " " 
			else:
				symbolString += "NON-INDEXED " 

			if "symbol_kind" in self.symbolIdsToData[key]:
				symbolString += self.symbolIdsToData[key]["symbol_kind"] + ": " 
			else:
				symbolString += "SYMBOL: " 

			if "name" in self.symbolIdsToData[key]:
				symbolString += self.symbolIdsToData[key]["name"]

			if "symbol_location" in self.symbolIdsToData[key]:
				symbolString += " at " + self.symbolIdsToData[key]["symbol_location"]

			if "scope_location" in self.symbolIdsToData[key]:
				symbolString += " with scope " + self.symbolIdsToData[key]["scope_location"]

			if "signature_location" in self.symbolIdsToData[key]:
				symbolString += " with signature " + self.symbolIdsToData[key]["signature_location"]

			symbolString = symbolString.strip()

			if symbolString:
				self.symbols.append(symbolString)

		self.localSymbols = []
		for key in self.localSymbolIdsToData:
			localSymbolString = ""

			if "name" in self.localSymbolIdsToData[key]:
				localSymbolString += self.localSymbolIdsToData[key]["name"]

			if localSymbolString and "local_symbol_locations" in self.localSymbolIdsToData[key]:	
				for location in self.localSymbolIdsToData[key]["local_symbol_locations"]:
					self.localSymbols.append(localSymbolString + " at " + location)
		
		self.references = []
		for key in self.referenceIdsToData:
			referenceString = ""
			
			if "reference_kind" in self.referenceIdsToData[key]:
				referenceString += self.referenceIdsToData[key]["reference_kind"] + ": " 
			else:
				referenceString += "REFERENCE: " 

			if "context_symbol_id" in self.referenceIdsToData[key] and self.referenceIdsToData[key]["context_symbol_id"] in self.symbolIdsToData:
				referenceString += self.symbolIdsToData[self.referenceIdsToData[key]["context_symbol_id"]]["name"]
			else:
				referenceString += "UNKNOWN SYMBOL" 

			referenceString += " -> "
			
			if "referenced_symbol_id" in self.referenceIdsToData[key] and self.referenceIdsToData[key]["referenced_symbol_id"] in self.symbolIdsToData:
				referenceString += self.symbolIdsToData[self.referenceIdsToData[key]["referenced_symbol_id"]]["name"]
			else:
				referenceString += "UNKNOWN SYMBOL" 

			if "reference_location" in self.referenceIdsToData[key]:
				referenceString += " at " + self.referenceIdsToData[key]["reference_location"]

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
			"id": symbolId, 
			"name": nameHierarchy.getDisplayString()
		}
		return symbolId


	def recordSymbolDefinitionKind(self, symbolId, symbolDefinitionKind):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]["definition_kind"] = symbolDefinitionKindToString(symbolDefinitionKind)


	def recordSymbolKind(self, symbolId, symbolKind):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]["symbol_kind"] = symbolKindToString(symbolKind)


	def recordSymbolLocation(self, symbolId, parseLocation):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]["symbol_location"] = parseLocation.toString()


	def recordSymbolScopeLocation(self, symbolId, parseLocation):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]["scope_location"] = parseLocation.toString()


	def recordSymbolSignatureLocation(self, symbolId, parseLocation):
		if symbolId in self.symbolIdsToData:
			self.symbolIdsToData[symbolId]["signature_location"] = parseLocation.toString()


	def recordReference(self, contextSymbolId, referencedSymbolId, referenceKind):
		serialized = str(contextSymbolId) + " -> " + str(referencedSymbolId) + "[" + str(referenceKind) + "]"
		if serialized in self.serializedReferencesToIds:
			return self.serializedReferencesToIds[serialized]

		referenceId = self.getNextElementId()
		self.serializedReferencesToIds[serialized] = referenceId
		self.referenceIdsToData[referenceId] = { 
			"id": referenceId, 
			"context_symbol_id": contextSymbolId,
			"referenced_symbol_id": referencedSymbolId,
			"reference_kind": referenceKindToString(referenceKind)
		}
		return referenceId


	def recordReferenceLocation(self, referenceId, parseLocation):
		if referenceId in self.referenceIdsToData:
			self.referenceIdsToData[referenceId]["reference_location"] = parseLocation.toString()


	def recordFile(self, filePath):
		serialized = filePath

		if serialized in self.serializedSymbolsToIds:
			return self.serializedSymbolsToIds[serialized]

		fileId = self.getNextElementId()
		self.serializedSymbolsToIds[serialized] = fileId
		self.symbolIdsToData[fileId] = { 
			"id": fileId, 
			"name": filePath,
			"symbol_kind": "FILE",
			"definition_kind": "INDEXED"
		}
		return fileId


	def recordFileLanguage(self, fileId, languageIdentifier):
		# FIXME: implement this one!
		return


	def recordLocalSymbol(self, name):
		if name in self.serializedLocalSymbolsToIds:
			return self.serializedLocalSymbolsToIds[serialized]

		localSymbolId = self.getNextElementId()
		self.serializedLocalSymbolsToIds[name] = localSymbolId
		self.localSymbolIdsToData[localSymbolId] = { 
			"id": localSymbolId,
			"name": name,
			"local_symbol_locations": []
		}
		return localSymbolId


	def recordLocalSymbolLocation(self, localSymbolId, parseLocation):
		if localSymbolId in self.localSymbolIdsToData:
			self.localSymbolIdsToData[localSymbolId]["local_symbol_locations"].append(parseLocation.toString())


	def recordCommentLocation(self, parseLocation):
		# FIXME: implement this one!
		return


	def recordError(self, message, fatal, parseLocation):
		# FIXME: implement this one!
		return


def symbolDefinitionKindToString(symbolDefinitionKind):
	if symbolDefinitionKind == srctrl.SYMBOL_ANNOTATION:
		return "EXPLICIT"
	if symbolDefinitionKind == srctrl.DEFINITION_IMPLICIT:
		return "IMPLICIT"
	return ""

def symbolKindToString(symbolKind):
	if symbolKind == srctrl.SYMBOL_TYPE:
		return "TYPE"
	if symbolKind == srctrl.SYMBOL_BUILTIN_TYPE:
		return "BUILTIN_TYPE"
	if symbolKind == srctrl.SYMBOL_NAMESPACE:
		return "NAMESPACE"
	if symbolKind == srctrl.SYMBOL_PACKAGE:
		return "PACKAGE"
	if symbolKind == srctrl.SYMBOL_STRUCT:
		return "STRUCT"
	if symbolKind == srctrl.SYMBOL_CLASS:
		return "CLASS"
	if symbolKind == srctrl.SYMBOL_INTERFACE:
		return "INTERFACE"
	if symbolKind == srctrl.SYMBOL_ANNOTATION:
		return "ANNOTATION"
	if symbolKind == srctrl.SYMBOL_GLOBAL_VARIABLE:
		return "GLOBAL_VARIABLE"
	if symbolKind == srctrl.SYMBOL_FIELD:
		return "FIELD"
	if symbolKind == srctrl.SYMBOL_FUNCTION:
		return "FUNCTION"
	if symbolKind == srctrl.SYMBOL_METHOD:
		return "METHOD"
	if symbolKind == srctrl.SYMBOL_ENUM:
		return "ENUM"
	if symbolKind == srctrl.SYMBOL_ENUM_CONSTANT:
		return "ENUM_CONSTANT"
	if symbolKind == srctrl.SYMBOL_TYPEDEF:
		return "TYPEDEF"
	if symbolKind == srctrl.SYMBOL_TEMPLATE_PARAMETER:
		return "TEMPLATE_PARAMETER"
	if symbolKind == srctrl.SYMBOL_TYPE_PARAMETER:
		return "TYPE_PARAMETER"
	if symbolKind == srctrl.SYMBOL_FILE:
		return "FILE"
	if symbolKind == srctrl.SYMBOL_MACRO:
		return "MACRO"
	if symbolKind == srctrl.SYMBOL_UNION:
		return "UNION"
	return ""


def referenceKindToString(referenceKind):
	if referenceKind == srctrl.REFERENCE_TYPE_USAGE:
		return "TYPE_USAGE"
	if referenceKind == srctrl.REFERENCE_USAGE:
		return "USAGE"
	if referenceKind == srctrl.REFERENCE_CALL:
		return "CALL"
	if referenceKind == srctrl.REFERENCE_INHERITANCE:
		return "INHERITANCE"
	if referenceKind == srctrl.REFERENCE_OVERRIDE:
		return "OVERRIDE"
	if referenceKind == srctrl.REFERENCE_TEMPLATE_ARGUMENT:
		return "TEMPLATE_ARGUMENT"
	if referenceKind == srctrl.REFERENCE_TYPE_ARGUMENT:
		return "TYPE_ARGUMENT"
	if referenceKind == srctrl.REFERENCE_TEMPLATE_DEFAULT_ARGUMENT:
		return "TEMPLATE_DEFAULT_ARGUMENT"
	if referenceKind == srctrl.REFERENCE_TEMPLATE_SPECIALIZATION:
		return "TEMPLATE_SPECIALIZATION"
	if referenceKind == srctrl.REFERENCE_TEMPLATE_MEMBER_SPECIALIZATION:
		return "TEMPLATE_MEMBER_SPECIALIZATION"
	if referenceKind == srctrl.REFERENCE_INCLUDE:
		return "INCLUDE"
	if referenceKind == srctrl.REFERENCE_IMPORT:
		return "IMPORT"
	if referenceKind == srctrl.REFERENCE_MACRO_USAGE:
		return "MACRO_USAGE"
	if referenceKind == srctrl.REFERENCE_ANNOTATION_USAGE:
		return "ANNOTATION_USAGE"
	return ""


if __name__ == '__main__':
    unittest.main()
