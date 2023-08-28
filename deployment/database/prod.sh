apt install postgresql postgresql-contrib
sudo -u postgres psql

\conninfo
\password postgres
CREATE DATABASE fairly;



pg_lsclusters
#format is pg_ctlcluster <version> <cluster> <action>
sudo pg_ctlcluster 9.6 main start

#restart postgresql service
sudo service postgresql restart
