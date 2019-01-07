import argparse
import indexer
import os
import sourcetraildb as srctrl


def main():
	parser = argparse.ArgumentParser(description="Index a Python source file and store the indexed data to a Sourcetrail database file.")
	parser.add_argument("--database-file-path", help="path to the generated Sourcetrail database file", type=str, required=True)
	parser.add_argument("--source-file-path", help="path to the source file to index", type=str, required=True)

	args = parser.parse_args()
	databaseFilePath = args.database_file_path
	sourceFilePath = args.source_file_path
	# TODO: make paths absolute if they are provided as relative paths

	if not srctrl.open(databaseFilePath):
		print("ERROR: " + srctrl.getLastError())

	if not srctrl.clear():
		print("ERROR: " + srctrl.getLastError())

	if srctrl.isEmpty():
		print("Loaded database is empty.")
	else:
		print("Loaded database contains data.")

	srctrl.beginTransaction()
	indexSourceFile(sourceFilePath)
	srctrl.commitTransaction()

	if not srctrl.close():
		print("ERROR: " + srctrl.getLastError())


def indexSourceFile(sourceFilePath):
	workingDirectory = os.getcwd()
	astVisitorClient = indexer.AstVisitorClient()
	indexer.indexSourceFile(sourceFilePath, workingDirectory, astVisitorClient, True)


if __name__ == '__main__':
	main()
