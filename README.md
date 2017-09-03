# daorys

## Run server using
`cd server`
`python server.py`

## Setup MongoDB using docker
* Pull mongoDB image `docker pull mongo`
* Run it in bridge/host network mode `docker run -d -p 27017:27017 --name some-mongo mongo --auth`
* Get into the container DB shell `docker exec -it some-mongo mongo admin`
* Create user for managing users `db.createUser({ user: 'userAdmin', pwd: 'gameofthrones', roles: [ { role: "userAdminAnyDatabase", db: "admin" } ] })`
* Login to that user `db.auth('userAdmin','gameofthrones')`
* Switch to DB named daorys `use daorys`
* Create user for daorys with read and write access `db.createUser({ user: 'daorys_rw', pwd: 'somepw', roles: [ { role: "readWrite", db: "daorys" } ] })`
* Login to that user `db.auth('daorys_rw','somepw')`
* Create DB collections users and messages `db.createCollection("users")` `db.createCollection("messages")`
