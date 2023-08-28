#!/bin/sh
export PGPASSWORD=postgres
export dbName=fairly

files=$(ls initdb)
for file in ${files}; do
	echo "--->executing $file"
	psql -h localhost -U postgres -d $dbName -f "initdb/${file}"
	#psql -h localhost -U postgres -d lbapi_test -f "initdb/${file}"
done
