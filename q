#!/usr/bin/env python
import xml.etree.ElementTree as ET
import argparse
import sqlite3
import cmd
import sys

db=None
cursor=None


# ####################################################
# Silly utility for wrapping quotes around strings - 
# so that SQL can feel properly informed that a string
# really is a string
# ####################################################
def qw(array):
	quoted=[]
	for element in array:
		quoted.append('"%s"' % element)
	return quoted

# ####################################################
# Do all the grunt work for creating the database
# which means
# 1) Loading the config(xml) file
# 2) Creating an in-memory SQLITE3 database
# 3) Creating the one-and-only table
# 4) Loading records into the DB from the source files
#
# The database is created from a set of sources, where
# each individual source may have its own distinguishing
# attributes. The individual source files are simply CSV
# files, containing a set of source-specific records. These
# sources are merged into the database, where the table 
# entry is the SOURCE ATTRIBUTES followed by the SOURCE-
# SPECIFIC records.  You better make sure that your TABLE
# definition includes the SOURCE ATTRIBUTES!
# ####################################################
def createDatabase(config):
	global db,cursor
	# ##############################################
	# STEP 1: Load the config
	#
	#  By default, sqllite returns unicode strings.
	#  Override the text_factory to get reg strings
	# ##############################################
	try:
		docTree = ET.parse(config.database)
	except (OSError, IOError) as e:
		sys.stderr.write("ERROR opening %s: %s\n" % (config.database, str(e)))
		sys.exit(1)	
	docRoot = docTree.getroot()

	# ##############################################
	# STEP 2: Create the in-memory SQLITE3 DB
	# Note: override the default and use have the
	#       text fields be normal strings rather 
	#       than unicode
	# ##############################################
	db = sqlite3.connect(":memory:")
	db.text_factory = str
	cursor = db.cursor()

	# ##############################################
	# STEP 3: Create the table
	# ##############################################
	for table in docRoot.findall("table"):
		tableName = table.attrib['name']
		fields = []
		for column in table:
			fields.append(column.attrib['name'])	
		query = "CREATE TABLE %s(%s)" % ( tableName, ",".join(fields))
		cursor.execute(query)
	
	# ##############################################
	# STEP 4: Load the sources
	# ##############################################
	for source in docRoot.findall("source"):
		tableName=None
		sourceFile=None
		sourceAttributes = []
		for key,value in source.attrib.iteritems():
			if key == 'file':
				sourceFile=value
			elif key == 'table':
				tableName=value	
			else:
				sourceAttributes.append(value)
		
		file = open(sourceFile, 'r')
		for line in file:
			if line.startswith('#'): continue
			fields = list(sourceAttributes)
			fields.extend( line.rstrip().split(',') )
			query = "INSERT INTO %s VALUES(%s)" % (tableName, ",".join(qw(fields)))
			cursor.execute(query)

# ################################################
# Setup a very basic command line processor
# ################################################
class isql(cmd.Cmd):
	def do_quit(self,args):
		'exits the program'
		sys.exit(0)

	def do_select(self, args):
		'query the database'
		try:
			for row in cursor.execute('SELECT ' + args):
				print "\t".join(str(field) for field in row)
		except Exception as e:
			print "ERROR: " + str(e)

# ################################################
# Main routine
# ################################################
if __name__ == "__main__":
	parser = argparse.ArgumentParser("SQLITE3 interface to a text-based database")
	parser.add_argument('-d', '--database', default="database.def")
	parser.add_argument('-q', '--query', dest='query')
	config = parser.parse_args()

	db = createDatabase(config)
	query = isql()
	query.prompt = 'isql> '
	if config.query:
		query.onecmd(config.query)
	else:
		query.cmdloop()
