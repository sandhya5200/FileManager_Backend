from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017"
connection = MongoClient(mongo_uri)
database = connection["File_Manager"]

users_collection = database["user"]
folders_collection = database["folders"]
files_collection = database["files"]