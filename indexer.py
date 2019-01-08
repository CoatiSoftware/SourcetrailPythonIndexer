import jedi
import json
import os
import sys

import sourcetraildb as srctrl


def indexSourceCode(sourceCode, workingDirectory, astVisitorClient, isVerbose):
	sourceFilePath = 'virtual_file.py'

	environment = jedi.api.environment.Environment(sys.executable)

	project = jedi.api.project.Project(workingDirectory)

	evaluator = jedi.evaluate.Evaluator(
		project, 
		environment=environment,
		script_path=workingDirectory
	)

	module_node = evaluator.parse(
		code=sourceCode,
		path=workingDirectory,
		cache=False,
		diff_cache=False
	)

	if (isVerbose):
		astVisitor = VerboseAstVisitor(astVisitorClient, environment, sourceFilePath, sourceCode) 
	else:
		astVisitor = AstVisitor(astVisitorClient, environment, sourceFilePath, sourceCode) 

	astVisitor.traverseNode(module_node)


def indexSourceFile(sourceFilePath, workingDirectory, astVisitorClient, isVerbose):
	sourceCode = ''
	with open(sourceFilePath, 'r') as input:
		sourceCode=input.read()

	project = jedi.api.project.Project(workingDirectory)
	environment = project.get_environment()

	evaluator = jedi.evaluate.Evaluator(
		project, 
		environment=environment,
		script_path=workingDirectory
	)

	module_node = evaluator.parse(
		code=sourceCode,
		path=workingDirectory,
		cache=False,
		diff_cache=False
	)

	if (isVerbose):
		astVisitor = VerboseAstVisitor(astVisitorClient, environment, sourceFilePath) 
	else:
		astVisitor = AstVisitor(astVisitorClient, environment, sourceFilePath) 

	astVisitor.traverseNode(module_node)


class AstVisitor:

	sourceFilePath = None
	sourceFileName = ''
	sourceFileContent = None
	client = None
	contextSymbolIdStack = []
	environment = None


	def __init__(self, client, environment, sourceFilePath, sourceFileContent = None):
		self.client = client
		self.environment = environment
		self.sourceFilePath = sourceFilePath.replace('\\', '/')
		self.sourceFileName = self.sourceFilePath.rsplit('/', 1).pop()
		self.sourceFileContent = sourceFileContent
		fileId = self.client.recordFile(self.sourceFilePath)
		if not fileId:
			print('ERROR: ' + srctrl.getLastError())
		self.contextSymbolIdStack.append(fileId)
		self.client.recordFileLanguage(fileId, 'python')


	def beginVisitName(self, node):
		if self.contextSymbolIdStack:
			for definition in self.getDefinitionsOfNode(node):
				if definition is not None:
					if not definition.line or not definition.column:
						# Early exit. For now we don't record references for names that don't have a valid definition location 
						continue

					if definition.type in ['class', 'function']:
						(startLine, startColumn) = node.start_pos
						if definition.line == startLine and definition.column == startColumn:
							# Early exit. We don't record references for locations of names that are definitions
							continue
					
						referenceId = -1

						if definition.type == 'class':
							referencedNameHierarchy = self.getNameHierarchyOfNode(definition._name.tree_name)

							referencedSymbolId = self.client.recordSymbol(referencedNameHierarchy)
							contextSymbolId = self.contextSymbolIdStack[len(self.contextSymbolIdStack) - 1]

							referenceId = self.client.recordReference(
								contextSymbolId,
								referencedSymbolId,
								srctrl.REFERENCE_TYPE_USAGE
							)

							# Record symbol kind. If the used type is within indexed code, this is not really necessary. In any other case, this is valuable info!
							self.client.recordSymbolKind(referencedSymbolId, srctrl.SYMBOL_CLASS)

						elif definition.type == 'function':
							if definition._name is not None and definition._name.tree_name is not None:
								referencedNameHierarchy = self.getNameHierarchyOfNode(definition._name.tree_name)

								referencedSymbolId = self.client.recordSymbol(referencedNameHierarchy)
								contextSymbolId = self.contextSymbolIdStack[len(self.contextSymbolIdStack) - 1]
								
								referenceKind = -1

								if True:
									nextNode = getNext(node)
									if nextNode is not None and nextNode.type == 'trailer':
										if len(nextNode.children) >= 2 and nextNode.children[0].value == '(' and nextNode.children[len(nextNode.children) - 1].value == ')':
											referenceKind = srctrl.REFERENCE_CALL

								if referenceKind is not -1:
									referenceId = self.client.recordReference(
										contextSymbolId,
										referencedSymbolId,
										referenceKind
									)
								
								# Record symbol kind. If the called function is within indexed code, this is not really necessary. In any other case, this is valuable info!
								self.client.recordSymbolKind(referencedSymbolId, srctrl.SYMBOL_FUNCTION)

						if referenceId == -1:
							continue
						elif referenceId == 0:
							print('ERROR: ' + srctrl.getLastError())
							continue
						else:
							self.client.recordReferenceLocation(referenceId, getSourceRangeOfNode(node))
							break # we just record usage of the first definition

					elif definition.type in ['param', 'statement']:
						localSymbolLocation = getSourceRangeOfNode(node)
						definitionLocation = getSourceRangeOfNode(definition._name.tree_name)
						localSymbolId = self.client.recordLocalSymbol(getLocalSymbolName(self.sourceFileName, definitionLocation))
						self.client.recordLocalSymbolLocation(localSymbolId, localSymbolLocation)
						# don't break here, because local variables can have multiple definitions (e.g. one in 'if' branch and one in 'else' branch)


	def endVisitName(self, node):
		pass


	def beginVisitClassdef(self, node):
		nameNode = getFirstDirectChildWithType(node, 'name')
		symbolId = self.client.recordSymbol(self.getNameHierarchyOfNode(node))
		self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
		self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_CLASS)
		self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))
		self.client.recordSymbolScopeLocation(symbolId, getSourceRangeOfNode(node))
		self.contextSymbolIdStack.append(symbolId)


	def endVisitClassdef(self, node):
		self.contextSymbolIdStack.pop()


	def beginVisitExprStmt(self, node):
		parentClassdefNode = getParentWithType(node, 'classdef')
		if parentClassdefNode is not None:
			definedNames = node.get_defined_names()
			for nameNode in definedNames:
				symbolId = self.client.recordSymbol(self.getNameHierarchyOfNode(nameNode))
				self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
				self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_FIELD)
				self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))


	def endVisitExprStmt(self, node):
		pass


	def beginVisitFuncdef(self, node):
		nameNode = getFirstDirectChildWithType(node, 'name')
		symbolId = self.client.recordSymbol(self.getNameHierarchyOfNode(node))
		self.client.recordSymbolDefinitionKind(symbolId, srctrl.DEFINITION_EXPLICIT)
		self.client.recordSymbolKind(symbolId, srctrl.SYMBOL_FUNCTION)
		self.client.recordSymbolLocation(symbolId, getSourceRangeOfNode(nameNode))
		self.client.recordSymbolScopeLocation(symbolId, getSourceRangeOfNode(node))
		self.contextSymbolIdStack.append(symbolId)


	def endVisitFuncdef(self, node):
		self.contextSymbolIdStack.pop()


	def traverseNode(self, node):
		if not node:
			return
		
		if node.type == 'name':
			self.beginVisitName(node)
		elif node.type == 'classdef':
			self.beginVisitClassdef(node)
		elif node.type == 'expr_stmt':
			self.beginVisitExprStmt(node)
		elif node.type == 'funcdef':
			self.beginVisitFuncdef(node)
		
		if hasattr(node, 'children'):
			for c in node.children:
				self.traverseNode(c)

		if node.type == 'name':
			self.endVisitName(node)
		elif node.type == 'classdef':
			self.endVisitClassdef(node)
		elif node.type == 'expr_stmt':
			self.endVisitExprStmt(node)
		elif node.type == 'funcdef':
			self.endVisitFuncdef(node)


	def getDefinitionsOfNode(self, node):
		(startLine, startColumn) = node.start_pos
		if self.sourceFileContent is None: # we are indexing a real file
			script = jedi.Script(
				source = None, 
				line = startLine, 
				column = startColumn, 
				path = self.sourceFilePath, 
				environment = self.environment
			) # todo: provide a sys_path parameter here
		else: # we are indexing a provided code snippet
			script = jedi.Script(
				source = self.sourceFileContent,
				line = startLine, 
				column = startColumn,
				environment = self.environment
			)
		return script.goto_assignments(follow_imports=True)

		
	def getNameHierarchyOfNode(self, node):
		if node is None:
			return None

		if node.type == 'name':
			nameNode = node
			parentNode = getNamedParentNode(node.parent)
		else:
			nameNode = getFirstDirectChildWithType(node, 'name')
			parentNode = getNamedParentNode(node)

		if nameNode is None:
			return None

		if parentNode is not None and parentNode.type == 'funcdef':
			grandParentNode = getNamedParentNode(parentNode)
			if grandParentNode is not None and grandParentNode.type == 'classdef':
				for definition in self.getDefinitionsOfNode(node):
					if definition.type == 'param':
						preceedingNode = definition._name.tree_name.parent.get_previous_sibling()
						if preceedingNode is not None and preceedingNode.type == 'operator':
							# 'node' is the first parameter of a member function (aka. 'self')
							node = grandParentNode
							parentNode =  getNamedParentNode(node)
							nameNode = getFirstDirectChildWithType(node, 'name')

		nameElement = NameElement(nameNode.value)

		if parentNode is not None:
			parentNodeNameHierarchy = self.getNameHierarchyOfNode(parentNode)
			if parentNodeNameHierarchy is not None:
				parentNodeNameHierarchy.nameElements.append(nameElement)
				return parentNodeNameHierarchy

		return NameHierarchy(nameElement, '.')


class VerboseAstVisitor(AstVisitor):

	def __init__(self, client, environment, sourceFilePath, sourceFileContent = None):
		AstVisitor.__init__(self, client, environment, sourceFilePath, sourceFileContent)
		self.indentationLevel = 0
		self.indentationToken = '| '


	def traverseNode(self, node):
		currentIndentation = ''
		for i in range(0, self.indentationLevel):
			currentIndentation += self.indentationToken

		print('AST: ' + currentIndentation + node.type)

		self.indentationLevel += 1
		AstVisitor.traverseNode(self, node)
		self.indentationLevel -= 1


class AstVisitorClient:

	indexedFileId = 0

	def __init__(self):
		if srctrl.isCompatible():
			print('Loaded database is compatible.')
		else:
			print('Loaded database is not compatible.')
			print('Supported DB Version: ' + str(srctrl.getSupportedDatabaseVersion()))
			print('Loaded DB Version: ' + str(srctrl.getLoadedDatabaseVersion()))


	def recordSymbol(self, nameHierarchy):
		symbolId = srctrl.recordSymbol(nameHierarchy.serialize())
		return symbolId


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


	def recordFile(self, filePath):
		self.indexedFileId = srctrl.recordFile(filePath)
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


	def recordCommentLocation(self, sourceRange):
		srctrl.recordCommentLocation(
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

	delimiter = ''


	def __init__(self, nameElement, delimiter):
		self.nameElements = []
		if not nameElement == None:
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

	name = ''
	prefix = ''
	postfix = ''


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


def getSourceRangeOfNode(node):
	startLine, startColumn = node.start_pos
	endLine, endColumn = node.end_pos
	return SourceRange(startLine, startColumn + 1, endLine, endColumn)


def getLocalSymbolName(sourceFileName, sourceRange):
	return sourceFileName + '<' + str(sourceRange.startLine) + ':' + str(sourceRange.startColumn) + '>'


def getNamedParentNode(node):
	if node is None:
		return None
	
	parentNode = node.parent
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
	
