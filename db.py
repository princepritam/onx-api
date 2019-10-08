from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/onx-api-db")

db = client.onx
