#!/bin/sh
#port=$(cat buildah/PORT)
port=5432

echo 'common commands:'
echo CREATE DATABASE taxed;
echo 'list tables: \dt;'
echo '\c taxed'
echo 'select * from users;'

echo UPDATE users SET status=50 WHERE id='2f617a75-...';

# connect from local psql
#psql -d taxed -U postgres -h localhost -p 7002

# connect from psql inside the postgresql container
#sudo docker exec -it taxed_container_1 /bin/bash -c "psql -d taxed -U postgres -h localhost"

# -d taxed to connect to database
psql postgresql://postgres:postgres@localhost:$port/fairly
