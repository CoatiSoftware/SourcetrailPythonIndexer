import argparse
import indexer
import os
import sourcetraildb as srctrl


def main():
	parser = argparse.ArgumentParser(description='Python source code indexer that generates a Sourcetrail compatible database.')
	parser.add_argument('--version', action='version', version='SourcetrailPythonIndexer {version}'.format(version=indexer.__version__))

	subparsers = parser.add_subparsers(title='commands', dest='command')

	indexCommandName = 'index'
	parserIndex = subparsers.add_parser(
		indexCommandName,
		help='Index a Python source file and store the indexed data to a Sourcetrail database file. Run "' + indexCommandName + ' -h" for more info on available arguments.'
	)
	parserIndex.add_argument('--source-file-path', help='path to the source file to index', type=str, required=True)
	parserIndex.add_argument('--database-file-path', help='path to the generated Sourcetrail database file', type=str, required=True)
	parserIndex.add_argument(
		'--environment-path',
		help='path to the Python executable or the directory that contains the Python environment that should be used to resolve dependencies within the indexed source '
			'code (if not specified the path to the currently used interpreter is used)',
		type=str,
		required=False
	)
	parserIndex.add_argument('--clear', help='clear the database before indexing', action='store_true', required=False)
	parserIndex.add_argument('--verbose', help='enable verbose console output', action='store_true', required=False)

	checkEnvironmentCommandName = 'check-environment'
	parserCheckEnvironment = subparsers.add_parser(
		checkEnvironmentCommandName,
		help='Check if the provided path specifies a valid Python environment. This command exits with code "0" if a valid Python environment has been provided, otherwise '
			'code "1" is returned. Run "' + checkEnvironmentCommandName + ' -h" for more info on available arguments.'
	)
	parserCheckEnvironment.add_argument(
		'--environment-path',
		help='path to the Python executable or the directory that contains the Python environment that should be checked for compatibility',
		type=str,
		required=True
	)

	args = parser.parse_args() # code exits here for "--version" and "--help"

	if args.command == indexCommandName:
		processIndexCommand(args)
	elif args.command == checkEnvironmentCommandName:
		processCheckEnvironmentCommand(args)


def processIndexCommand(args):
	workingDirectory = os.getcwd()

	if not indexer.isSourcetrailDBVersionCompatible(True):
		return

	databaseFilePath = args.database_file_path
	if not os.path.isabs(databaseFilePath):
		databaseFilePath = os.path.join(workingDirectory, databaseFilePath)

	sourceFilePath = args.source_file_path
	if not os.path.isabs(sourceFilePath):
		sourceFilePath = os.path.join(workingDirectory, sourceFilePath)

	environmentPath = args.environment_path
	if environmentPath is not None and not os.path.isabs(environmentPath):
		environmentPath = os.path.join(workingDirectory, environmentPath)

	if not srctrl.open(databaseFilePath):
		print('ERROR: ' + srctrl.getLastError())

	if args.clear:
		if args.verbose:
			print('INFO: Clearing database...')
		if not srctrl.clear():
			print('ERROR: ' + srctrl.getLastError())
		else:
			if args.verbose:
				print('INFO: Clearing done.')

	if args.verbose:
		if srctrl.isEmpty():
			print('INFO: Loaded database is empty.')
		else:
			print('INFO: Loaded database contains data.')

	srctrl.beginTransaction()
	indexSourceFile(sourceFilePath, environmentPath, workingDirectory, args.verbose)
	srctrl.commitTransaction()

	if not srctrl.close():
		print('ERROR: ' + srctrl.getLastError())


def processCheckEnvironmentCommand(args):
	workingDirectory = os.getcwd()

	environmentPath = args.environment_path
	if environmentPath is not None and not os.path.isabs(environmentPath):
		environmentPath = os.path.join(workingDirectory, environmentPath)

	if indexer.isValidEnvironment(environmentPath):
		print('Provided path is a valid Python environment.')
		return 0

	print('Provided path is not a valid Python environment.')
	return 1


def indexSourceFile(sourceFilePath, environmentPath, workingDirectory, verbose):
	astVisitorClient = indexer.AstVisitorClient()
	indexer.indexSourceFile(sourceFilePath, environmentPath, workingDirectory, astVisitorClient, verbose)


if __name__ == '__main__':
	main()
