FROM postgres:15.2
ENV POSTGRES_USER postgres
ENV POSTGRES_PASSWORD postgres
ENV POSTGRES_DB fairly
ENV PGDATA /var/lib/postgresql/pgdata
#ADD 00-db-init.sql /docker-entrypoint-initdb.d/
#ADD 11-db-characters.pgsql /docker-entrypoint-initdb.d/
#EXPOSE 5432
