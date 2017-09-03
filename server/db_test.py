import pymongo
from pymongo import MongoClient
dbusername = "daorys_rw"
dbpw = "somepw"

connection = pymongo.MongoClient('127.0.0.1', 27017)
db = connection["daorys"]
db.authenticate(dbusername, dbpw)
record = db.users.find_one({"username":"rahul1"})
if record:
    print "found!!"
else:
    print "not found"


#client = MongoClient('mongodb://{}:{}@localhost:27017'.format(dbusername,dbpw))
#db = client.daorys
#db.users.find_one({"username":"rahul"})
