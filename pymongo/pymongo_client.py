#!/usr/bin/env python

# Automated mongodb data dump
# installing pymongo
# https://pypi.org/project/pymongo/


# Author's github: https://github.com/Asperheek/
# Usage: ./pymongo_client.py 192.168.137.110 27017

import sys
import pymongo

def main():
	IP = str(sys.argv[1]) 
	port = int(sys.argv[2])
	client = pymongo.MongoClient(IP, port)
	print("==========================Script v1.0==========================")
	print("=======================Author: Asperheek=======================")
# server_info() function to obtain the data about the MongoDB server instance.
	print ("==========================Server Info==========================")
	print(client.server_info())

# list_database_names() to get a list of all the databases.
	print("=======================List of Databases=======================")
	print(client.list_database_names())

# selecting the database and listing its collections.
	print("==========================Collections==========================")
	for db in client.list_database_names():
		database = client[db]
		print("Collections of the database " + db + ":")
		print(database.list_collection_names(include_system_collections=False))


	doc = raw_input("Do you want to continue by finding the documents inside the collections? y/n : ")
	if(doc == "y" or doc == "Y"):
		for db in client.list_database_names():
			dbx = client[db]
			col = dbx.list_collection_names(include_system_collections=False)
			for i in col:
				print("===============================================================")
				print(i)
				print("===============================================================")
				collection = dbx[i]
				for docx in collection.find():
					print(docx)		
	else:
		raise SystemExit



if __name__ == '__main__':
	main()
