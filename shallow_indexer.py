import parso
import json
import os
from enum import Enum
import sys

import sourcetraildb as srctrl
from _version import __version__
from _version import _sourcetrail_db_version

from indexer import AstVisitorClient
from indexer import SourceRange
from indexer import NameHierarchy
from indexer import NameElement
from indexer import NameHierarchyEncoder


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

class ContextType(Enum):
	FILE = 1
	MODULE = 2
	CLASS = 3
	FUNCTION = 4
	METHOD = 5


class ContextInfo:

	def __init__(self, id, contextType, name, node):
		self.id = id
		self.name = name
		self.node = node
		self.selfParamName = None
		self.localSymbolNames = []
		self.contextType = contextType


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
		self.contextStack.append(ContextInfo(fileId, ContextType.FILE, self.sourceFilePath, None))

		moduleNameHierarchy = self.getNameHierarchyFromModuleFilePath(self.sourceFilePath)
		if moduleNameHierarchy is not None:
			moduleId = self.client.recordSymbol(moduleNameHierarchy)
			self.client.recordSymbolDefinitionKind(moduleId, srctrl.DEFINITION_EXPLICIT)
			self.client.recordSymbolKind(moduleId, srctrl.SYMBOL_MODULE)
			self.contextStack.append(ContextInfo(moduleId, ContextType.MODULE, moduleNameHierarchy.getDisplayString(), None))


	def traverseNode(self, node):
		if node is None:
			return

		if node.type == 'classdef':
			self.traverseClassdef(node)
		elif node.type == 'funcdef':
			self.traverseFuncdef(node)
		elif node.type == 'param':
			self.traverseParam(node)
		else:
			if node.type == 'name':
				self.beginVisitName(node)
			elif node.type == 'string':
				self.beginVisitString(node)
			elif node.type == 'error_leaf':
				self.beginVisitErrorLeaf(node)

			if hasattr(node, 'children'):
				for c in node.children:
					self.traverseNode(c)

			if node.type == 'name':
				self.endVisitName(node)
			elif node.type == 'string':
				self.endVisitString(node)
			elif node.type == 'error_leaf':
				self.endVisitErrorLeaf(node)

#----------------

	def traverseClassdef(self, node):
		if node is None:
			return

		self.beginVisitClassdef(node)
		#get_super_arglist()

		self.traverseNode(node.get_suite())

		self.endVisitClassdef(node)


	def traverseFuncdef(self, node):
		if node is None:
			return

		self.beginVisitFuncdef(node)

		for n in node.get_params():
			self.traverseNode(n)
		self.traverseNode(node.get_suite())

		self.endVisitFuncdef(node)


	def traverseParam(self, node):
		if node is None:
			return

		self.beginVisitParam(node)

		self.traverseNode(node.default)

		self.endVisitParam(node)

#----------------

	def beginVisitClassdef(self, node):
		nameNode = node.name

		symbolNameHierarchy = self.getNameHierarchyOfNode(nameNode)
		if symbolNameHierarchy is None:
			symbolNameHierarchy = getNameHierarchyForUnsolvedSymbol()

		symbolId = self.client.recordSymbol(symbolNameHierarchy)
		self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
		self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_CLASS)
		self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))
		self.client.recordSymbolScopeLocation(symbolId, getSourceRangeOfNode(node))
		self.contextStack.append(ContextInfo(symbolId, ContextType.CLASS, symbolNameHierarchy.getDisplayString(), node))


	def endVisitClassdef(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitFuncdef(self, node):
		nameNode = node.name

		symbolNameHierarchy = self.getNameHierarchyOfNode(nameNode)
		if symbolNameHierarchy is None:
			symbolNameHierarchy = getNameHierarchyForUnsolvedSymbol()

		selfParamName = None
		localSymbolNames = []

		contextType = ContextType.FUNCTION
		if self.contextStack[-1].contextType == ContextType.CLASS:
			contextType = ContextType.METHOD

		for param in node.get_params():
			if contextType == ContextType.METHOD and selfParamName is None:
				selfParamName = param.name.value
			localSymbolNames.append(param.name.value)

		symbolId = self.client.recordSymbol(symbolNameHierarchy)
		self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
		self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_FUNCTION)
		self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))
		self.client.recordSymbolScopeLocation(symbolId, getSourceRangeOfNode(node))
		contextInfo = ContextInfo(symbolId, contextType, symbolNameHierarchy.getDisplayString(), node)
		contextInfo.selfParamName = selfParamName
		contextInfo.localSymbolNames.extend(localSymbolNames)
		self.contextStack.append(contextInfo)


	def endVisitFuncdef(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitParam(self, node):
		nameNode = node.name
		localSymbolId = self.client.recordLocalSymbol(self.getLocalSymbolName(nameNode))
		self.client.recordLocalSymbolLocation(localSymbolId, getSourceRangeOfNode(nameNode))


	def endVisitParam(self, node):
		if len(self.contextStack) > 0:
			contextNode = self.contextStack[-1].node
			if node == contextNode:
				self.contextStack.pop()


	def beginVisitName(self, node):
		if len(self.contextStack) == 0:
			return

		if node.value in ['True', 'False', 'None']: # these are not parsed as "keywords" in Python 2
			return

		if node.is_definition():
			namedDefinitionParentNode = getParentWithTypeInList(node, ['classdef', 'funcdef'])
			if namedDefinitionParentNode is not None:
				if namedDefinitionParentNode.type in ['classdef']:
					if getNamedParentNode(node) == namedDefinitionParentNode:
						# definition is not local to some other field instantiation but instead it is a static member variable
						# node is the definition of the static member variable
						symbolNameHierarchy = self.getNameHierarchyOfNode(node)
						if symbolNameHierarchy is not None:
							symbolId = self.client.recordSymbol(symbolNameHierarchy)
							self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_FIELD)
							self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
							self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(node))
							return
				elif namedDefinitionParentNode.type in ['funcdef']:
					# definition may be a non-static member variable
					if node.parent is not None and node.parent.type == 'trailer':
						potentialSelfParamNode = getNamedParentNode(node)
						if potentialSelfParamNode is not None and getFirstDirectChildWithType(potentialSelfParamNode, 'name').value == self.contextStack[-1].selfParamName:
							# definition is a non-static member variable
							symbolNameHierarchy = self.getNameHierarchyOfNode(node)
							if symbolNameHierarchy is not None:
								symbolId = self.client.recordSymbol(symbolNameHierarchy)
								self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_FIELD)
								self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
								self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(node))
								return
					localSymbolId = self.client.recordLocalSymbol(self.getLocalSymbolName(node))
					self.client.recordLocalSymbolLocation(localSymbolId, getSourceRangeOfNode(node))
					return
			else:
				symbolNameHierarchy = self.getNameHierarchyOfNode(node)
				if symbolNameHierarchy is not None:
					symbolId = self.client.recordSymbol(symbolNameHierarchy)
					self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_GLOBAL_VARIABLE)
					self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
					self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(node))
					return

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

#----------------

	def getLocalSymbolName(self, nameNode):
		return str(self.contextStack[-1].name) + '<' + nameNode.value + '>'


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

		if self.contextStack[-1].contextType == ContextType.METHOD:
			potentialSelfNode = getNamedParentNode(node)
			if potentialSelfNode is not None:
				potentialSelfNameNode = getFirstDirectChildWithType(potentialSelfNode, 'name')
				if potentialSelfNameNode is not None and potentialSelfNameNode.value == self.contextStack[-1].selfParamName:
					parentNode = self.contextStack[-2].node

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
		if node is None:
			return

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