import argparse
import indexer
import os
import sourcetraildb as srctrl


def main():
	parser = argparse.ArgumentParser(description='Index a Python source file and store the indexed data to a Sourcetrail database file.')
	parser.add_argument('--source-file-path', help='path to the source file to index', type=str, required=True)
	parser.add_argument('--database-file-path', help='path to the generated Sourcetrail database file', type=str, required=True)
	parser.add_argument(
		'--environment-directory-path',
		help='path to the directory that contains the Python environment that should be used to resolve dependencies within the indexed source '
			'code (if not specified the path to the currently used interpreter is used)',
		type=str,
		required=False
	)
	parser.add_argument('--clear', help='clear the database before indexing', action='store_true', required=False)
	parser.add_argument('--verbose', help='enable verbose console output', action='store_true', required=False)

	args = parser.parse_args()

	workingDirectory = os.getcwd()

	databaseFilePath = args.database_file_path
	if not os.path.isabs(databaseFilePath):
		databaseFilePath = os.path.join(workingDirectory, databaseFilePath)

	sourceFilePath = args.source_file_path
	if not os.path.isabs(sourceFilePath):
		sourceFilePath = os.path.join(workingDirectory, sourceFilePath)

	environmentDirectoryPath = args.environment_directory_path
	if environmentDirectoryPath is not None and not os.path.isabs(environmentDirectoryPath):
		environmentDirectoryPath = os.path.join(workingDirectory, environmentDirectoryPath)

	if not srctrl.open(databaseFilePath):
		print('ERROR: ' + srctrl.getLastError())

	if args.clear:
		if args.verbose:
			print('Clearing database...')
		if not srctrl.clear():
			print('ERROR: ' + srctrl.getLastError())
		else:
			if args.verbose:
				print('Clearing done.')

	if args.verbose:
		if srctrl.isEmpty():
			print('Loaded database is empty.')
		else:
			print('Loaded database contains data.')

	srctrl.beginTransaction()
	indexSourceFile(sourceFilePath, environmentDirectoryPath, workingDirectory, args.verbose)
	srctrl.commitTransaction()

	if not srctrl.close():
		print('ERROR: ' + srctrl.getLastError())


def indexSourceFile(sourceFilePath, environmentDirectoryPath, workingDirectory, verbose):
	astVisitorClient = indexer.AstVisitorClient()
	indexer.indexSourceFile(sourceFilePath, environmentDirectoryPath, workingDirectory, astVisitorClient, verbose)


if __name__ == '__main__':
	main()
