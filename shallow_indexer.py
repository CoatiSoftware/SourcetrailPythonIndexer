import parso
import json
import os
import sys

import sourcetraildb as srctrl
from _version import __version__
from _version import _sourcetrail_db_version


_virtualFilePath = 'virtual_file.py'


def isSourcetrailDBVersionCompatible(allowLogging = False):
	requiredVersion = _sourcetrail_db_version

	try:
		usedVersion = srctrl.getVersionString()
	except AttributeError:
		if allowLogging:
			print('ERROR: Used version of SourcetrailDB is incompatible to what is required by this version of SourcetrailPythonIndexer (' + requiredVersion + ').')
		return False

	if usedVersion != requiredVersion:
		if allowLogging:
			print('ERROR: Used version of SourcetrailDB (' + usedVersion + ') is incompatible to what is required by this version of SourcetrailPythonIndexer (' + requiredVersion + ').')
		return False
	return True


def indexSourceCode(sourceCode, workingDirectory, astVisitorClient, isVerbose, sysPath = None):
	sourceFilePath = _virtualFilePath

	moduleNode = parso.parse(sourceCode)

	if (isVerbose):
		astVisitor = VerboseAstVisitor(astVisitorClient, sourceFilePath, sourceCode, sysPath)
	else:
		astVisitor = AstVisitor(astVisitorClient, sourceFilePath, sourceCode, sysPath)

	astVisitor.traverseNode(moduleNode)


def indexSourceFile(sourceFilePath, environmentDirectoryPath, workingDirectory, astVisitorClient, isVerbose):

	if isVerbose:
		print('INFO: Indexing source file "' + sourceFilePath + '".')

	sourceCode = ''
	with open(sourceFilePath, 'r', encoding='utf-8') as input:
		sourceCode=input.read()

	moduleNode = parso.parse(sourceCode)

	if (isVerbose):
		astVisitor = VerboseAstVisitor(astVisitorClient, sourceFilePath)
	else:
		astVisitor = AstVisitor(astVisitorClient, sourceFilePath)

	astVisitor.traverseNode(moduleNode)


class ContextInfo:

	def __init__(self, id, name, node):
		self.id = id
		self.name = name
		self.node = node


class AstVisitor:

	def __init__(self, client, sourceFilePath, sourceFileContent = None, sysPath = None):

		self.client = client

		self.sourceFilePath = sourceFilePath
		if sourceFilePath != _virtualFilePath:
			self.sourceFilePath = os.path.abspath(self.sourceFilePath)

		self.sourceFileName = os.path.split(self.sourceFilePath)[-1]
		self.sourceFileContent = sourceFileContent

		packageRootPath = os.path.dirname(self.sourceFilePath)
		while os.path.exists(os.path.join(packageRootPath, '__init__.py')):
			packageRootPath =  os.path.dirname(packageRootPath)
		self.sysPath = [packageRootPath]

		if sysPath is not None:
			self.sysPath.extend(sysPath)
#		else:
#			baseSysPath = evaluator.project._get_base_sys_path(self.environment)
#			baseSysPath.sort(reverse=True)
#			self.sysPath.extend(baseSysPath)
		self.sysPath = list(filter(None, self.sysPath))

		self.contextStack = []

		fileId = self.client.recordFile(self.sourceFilePath)
		if fileId == 0:
			print('ERROR: ' + srctrl.getLastError())
		self.client.recordFileLanguage(fileId, 'python')
		self.contextStack.append(ContextInfo(fileId, self.sourceFilePath, None))

		moduleNameHierarchy = self.getNameHierarchyFromModuleFilePath(self.sourceFilePath)
		if moduleNameHierarchy is not None:
			moduleId = self.client.recordSymbol(moduleNameHierarchy)
			self.client.recordSymbolDefinitionKind(moduleId, srctrl.DEFINITION_EXPLICIT)
			self.client.recordSymbolKind(moduleId, srctrl.SYMBOL_MODULE)
			self.contextStack.append(ContextInfo(moduleId, moduleNameHierarchy.getDisplayString(), None))


	def traverseNode(self, node):
		if node is None:
			return

		if node.type == 'funcdef':
			self.traverseFuncdefNode(node)
			return

		if node.type == 'classdef':
			self.beginVisitClassdef(node)
		elif node.type == 'name':
			self.beginVisitName(node)
		elif node.type == 'string':
			self.beginVisitString(node)
		elif node.type == 'error_leaf':
			self.beginVisitErrorLeaf(node)

		if hasattr(node, 'children'):
			for c in node.children:
				self.traverseNode(c)

		if node.type == 'classdef':
			self.endVisitClassdef(node)
		elif node.type == 'name':
			self.endVisitName(node)
		elif node.type == 'string':
			self.endVisitString(node)
		elif node.type == 'error_leaf':
			self.endVisitErrorLeaf(node)

		
	def traverseFuncdefNode(self, node):
		if node is None:
			return
			
		self.beginVisitFuncdef(node)

		childTypes = ['pre_params', 'params', 'post_params']

		if hasattr(node, 'children'):
			for c in node.children:
				
				self.traverseNode(c)

		self.endVisitFuncdef(node)


	def beginVisitClassdef(self, node):
		nameNode = getFirstDirectChildWithType(node, 'name')

		symbolNameHierarchy = self.getNameHierarchyOfNode(nameNode)
		if symbolNameHierarchy is None:
			symbolNameHierarchy = getNameHierarchyForUnsolvedSymbol()

		symbolId = self.client.recordSymbol(symbolNameHierarchy)
		self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
		self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_CLASS)
		self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))
		self.client.recordSymbolScopeLocation(symbolId, getSourceRangeOfNode(node))
		self.contextStack.append(ContextInfo(symbolId, symbolNameHierarchy.getDisplayString(), node))


	def endVisitClassdef(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitFuncdef(self, node):
		nameNode = getFirstDirectChildWithType(node, 'name')

		symbolNameHierarchy = self.getNameHierarchyOfNode(nameNode)
		if symbolNameHierarchy is None:
			symbolNameHierarchy = getNameHierarchyForUnsolvedSymbol()

		symbolId = self.client.recordSymbol(symbolNameHierarchy)
		self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
		self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_FUNCTION)
		self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))
		self.client.recordSymbolScopeLocation(symbolId, getSourceRangeOfNode(node))
		self.contextStack.append(ContextInfo(symbolId, symbolNameHierarchy.getDisplayString(), node))


	def endVisitFuncdef(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitName(self, node):
		if len(self.contextStack) == 0:
			return

		if node.value in ['True', 'False', 'None']: # these are not parsed as "keywords" in Python 2
			return

		if node.parent is not None and node.parent.type in ['classdef', 'funcdef']:
			pass
		else:
			self.client.recordReferenceToUnsolvedSymhol(self.contextStack[-1].id, srctrl.REFERENCE_USAGE, getSourceRangeOfNode(node))


	def endVisitName(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitString(self, node):
		sourceRange = getSourceRangeOfNode(node)
		if sourceRange.startLine != sourceRange.endLine:
			self.client.recordAtomicSourceRange(sourceRange)


	def endVisitString(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitErrorLeaf(self, node):
		self.client.recordError('Unexpected token of type "' + node.token_type + '" encountered.', False, getSourceRangeOfNode(node))


	def endVisitErrorLeaf(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def getLocalSymbolName(self, definition):
		definitionNameNode = definition._name.tree_name

		definitionModulePath = definition.module_path
		if definitionModulePath is None:
			if self.sourceFilePath == _virtualFilePath:
				definitionModulePath = self.sourceFilePath

		contextName = ''
		if definitionModulePath is not None:
			parentFuncdef = getParentWithType(definitionNameNode, 'funcdef')
			if parentFuncdef is not None:
				parentFuncdefNameNode = getFirstDirectChildWithType(parentFuncdef, 'name')
				if parentFuncdefNameNode is not None:
					parentFuncdefNameHierarchy = self.getNameHierarchyOfNode(parentFuncdefNameNode)
					if parentFuncdefNameHierarchy is not None:
						contextName = parentFuncdefNameHierarchy.getDisplayString()

		if len(contextName) == 0:
			contextName = str(self.contextStack[-1].name)

		return contextName + '<' + definitionNameNode.value + '>'


	def getNameHierarchyFromModuleFilePath(self, filePath):
		if filePath is None:
			return None

		if filePath == _virtualFilePath:
			return NameHierarchy(NameElement(os.path.splitext(_virtualFilePath)[0]), '.')

		filePath = os.path.abspath(filePath)
		# First remove the suffix.
		for suffix in ['.py']:
			if filePath.endswith(suffix):
				filePath = filePath[:-len(suffix)]
				break

		for p in self.sysPath:
			if filePath.startswith(p):
				rest = filePath[len(p):]
				if rest.startswith(os.path.sep):
					# Remove a slash in cases it's still there.
					rest = rest[1:]
				if rest:
					split = rest.split(os.path.sep)
					for string in split:
						if not string:
							return None

					if split[-1] == '__init__':
						split = split[:-1]

					nameHierarchy = None
					for namePart in split:
						if nameHierarchy is None:
							nameHierarchy = NameHierarchy(NameElement(namePart), '.')
						else:
							nameHierarchy.nameElements.append(NameElement(namePart))
					return nameHierarchy

		return None


	def getNameHierarchyOfNode(self, node):
		if node is None:
			return None

		if node.type == 'name':
			nameNode = node
		else:
			nameNode = getFirstDirectChildWithType(node, 'name')

		if nameNode is None:
			return None

		parentNode = getParentWithTypeInList(nameNode.parent, ['classdef', 'funcdef'])
		nameElement = NameElement(nameNode.value)

		if parentNode is not None:
			parentNodeNameHierarchy = self.getNameHierarchyOfNode(parentNode)
			if parentNodeNameHierarchy is None:
				return None
			parentNodeNameHierarchy.nameElements.append(nameElement)
			return parentNodeNameHierarchy

		nameHierarchy = self.getNameHierarchyFromModuleFilePath(self.sourceFilePath)
		if nameHierarchy is None:
			return None
		nameHierarchy.nameElements.append(nameElement)
		return nameHierarchy

		return None


class VerboseAstVisitor(AstVisitor):

	def __init__(self, client, sourceFilePath, sourceFileContent = None, sysPath = None):
		AstVisitor.__init__(self, client, sourceFilePath, sourceFileContent, sysPath)
		self.indentationLevel = 0
		self.indentationToken = '| '


	def traverseNode(self, node):
		currentString = ''
		for i in range(0, self.indentationLevel):
			currentString += self.indentationToken

		currentString += node.type

		if hasattr(node, 'value'):
			currentString += ' (' + repr(node.value) + ')'

		currentString += ' ' + getSourceRangeOfNode(node).toString()

		print('AST: ' + currentString)

		self.indentationLevel += 1
		AstVisitor.traverseNode(self, node)
		self.indentationLevel -= 1


class AstVisitorClient:

	def __init__(self):
		self.indexedFileId = 0
		if srctrl.isCompatible():
			print('INFO: Loaded database is compatible.')
		else:
			print('WARNING: Loaded database is not compatible.')
			print('INFO: Supported DB Version: ' + str(srctrl.getSupportedDatabaseVersion()))
			print('INFO: Loaded DB Version: ' + str(srctrl.getLoadedDatabaseVersion()))


	def recordSymbol(self, nameHierarchy):
		if nameHierarchy is not None:
			symbolId = srctrl.recordSymbol(nameHierarchy.serialize())
			return symbolId
		return 0


	def recordSymbolDefinitionKind(self, symbolId, symbolDefinitionKind):
		srctrl.recordSymbolDefinitionKind(symbolId, symbolDefinitionKind)


	def recordSymbolKind(self, symbolId, symbolKind):
		srctrl.recordSymbolKind(symbolId, symbolKind)


	def recordSymbolLocation(self, symbolId, sourceRange):
		srctrl.recordSymbolLocation(
			symbolId,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordSymbolScopeLocation(self, symbolId, sourceRange):
		srctrl.recordSymbolScopeLocation(
			symbolId,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordSymbolSignatureLocation(self, symbolId, sourceRange):
		srctrl.recordSymbolSignatureLocation(
			symbolId,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordReference(self, contextSymbolId, referencedSymbolId, referenceKind):
		return srctrl.recordReference(
			contextSymbolId,
			referencedSymbolId,
			referenceKind
		)


	def recordReferenceLocation(self, referenceId, sourceRange):
		srctrl.recordReferenceLocation(
			referenceId,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordReferenceIsAmbiuous(self, referenceId):
		return srctrl.recordReferenceIsAmbiuous(referenceId)


	def recordReferenceToUnsolvedSymhol(self, contextSymbolId, referenceKind, sourceRange):
		return srctrl.recordReferenceToUnsolvedSymhol(
			contextSymbolId,
			referenceKind,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordQualifierLocation(self, referencedSymbolId, sourceRange):
		return srctrl.recordQualifierLocation(
			referencedSymbolId,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordFile(self, filePath):
		self.indexedFileId = srctrl.recordFile(filePath.replace('\\', '/'))
		srctrl.recordFileLanguage(self.indexedFileId, 'python')
		return self.indexedFileId


	def recordFileLanguage(self, fileId, languageIdentifier):
		srctrl.recordFileLanguage(fileId, languageIdentifier)


	def recordLocalSymbol(self, name):
		return srctrl.recordLocalSymbol(name)


	def recordLocalSymbolLocation(self, localSymbolId, sourceRange):
		srctrl.recordLocalSymbolLocation(
			localSymbolId,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordAtomicSourceRange(self, sourceRange):
		srctrl.recordAtomicSourceRange(
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


	def recordError(self, message, fatal, sourceRange):
		srctrl.recordError(
			message,
			fatal,
			self.indexedFileId,
			sourceRange.startLine,
			sourceRange.startColumn,
			sourceRange.endLine,
			sourceRange.endColumn
		)


class SourceRange:

	def __init__(self, startLine, startColumn, endLine, endColumn):
		self.startLine = startLine
		self.startColumn = startColumn
		self.endLine = endLine
		self.endColumn = endColumn


	def toString(self):
		return '[' + str(self.startLine) + ':' + str(self.startColumn) + '|' + str(self.endLine) + ':' + str(self.endColumn) + ']'


class NameHierarchy():

	unsolvedSymbolName = 'unsolved symbol' # this name should not collide with normal symbol name, because they cannot contain space characters

	def __init__(self, nameElement, delimiter):
		self.nameElements = []
		if nameElement is not None:
			self.nameElements.append(nameElement)
		self.delimiter = delimiter


	def serialize(self):
		return json.dumps(self, cls=NameHierarchyEncoder)


	def getDisplayString(self):
		displayString = ''
		isFirst = True
		for nameElement in self.nameElements:
			if not isFirst:
				displayString += self.delimiter
			isFirst = False
			if len(nameElement.prefix) > 0:
				displayString += nameElement.prefix + ' '
			displayString += nameElement.name
			if len(nameElement.postfix) > 0:
				displayString += nameElement.postfix
		return displayString


class NameElement:

	def __init__(self, name, prefix = '', postfix = ''):
		self.name = name
		self.prefix = prefix
		self.postfix = postfix


class NameHierarchyEncoder(json.JSONEncoder):

	def default(self, obj):
		if isinstance(obj, NameHierarchy):
			return {
				'name_delimiter': obj.delimiter,
				'name_elements': [nameElement.__dict__ for nameElement in obj.nameElements]
			}
		# Let the base class default method raise the TypeError
		return json.JSONEncoder.default(self, obj)


def getNameHierarchyForUnsolvedSymbol():
	return NameHierarchy(NameElement(NameHierarchy.unsolvedSymbolName), '.')


def isQualifierNode(node):
	nextNode = getNext(node)
	if nextNode is not None and nextNode.type == 'trailer':
		nextNode = getNext(nextNode)
	if nextNode is not None and nextNode.type == 'operator' and nextNode.value == '.':
		return True
	return False


def getSourceRangeOfNode(node):
	startLine, startColumn = node.start_pos
	endLine, endColumn = node.end_pos
	return SourceRange(startLine, startColumn + 1, endLine, endColumn)


def getNamedParentNode(node):
	if node is None:
		return None

	parentNode = node.parent

	if node.type == 'name' and parentNode is not None:
		parentNode = parentNode.parent

	while parentNode is not None:
		if getFirstDirectChildWithType(parentNode, 'name') is not None:
			return parentNode
		parentNode = parentNode.parent

	return None


def getParentWithType(node, type):
	if node == None:
		return None
	parentNode = node.parent
	if parentNode == None:
		return None
	if parentNode.type == type:
		return parentNode
	return getParentWithType(parentNode, type)


def getParentWithTypeInList(node, typeList):
	if node == None:
		return None
	parentNode = node.parent
	if parentNode == None:
		return None
	if parentNode.type in typeList:
		return parentNode
	return getParentWithTypeInList(parentNode, typeList)


def getFirstDirectChildWithType(node, type):
	for c in node.children:
		if c.type == type:
			return c
	return None


def getDirectChildrenWithType(node, type):
	children = []
	for c in node.children:
		if c.type == type:
			children.append(c)
	return children


def getNext(node):
	if hasattr(node, 'children'):
		for c in node.children:
			return c

	siblingSource = node
	while siblingSource is not None and siblingSource.parent is not None:
		sibling = siblingSource.get_next_sibling()
		if sibling is not None:
			return sibling
		siblingSource = siblingSource.parent

	return None
