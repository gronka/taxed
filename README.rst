FairlyTaxed API
====

See the 'Operations' repository for documentation and testing (not public for security).

requires at least python version 3.6 (probably higher)

pip install -r requirements.txt
pip install -e .
create /taxed/certs/creds.toml

mkdir -p /taxed/data/{challenge,comparables,map,street}


Renamed routes from original:
* /processing/search_addres -> /challenge.request
* /processing/approve_search -> /challenge.paid


Deployment:
As a general rule, you probably want to:

* Run uvicorn --reload from the command line for local development.
* Run gunicorn -k uvicorn.workers.UvicornWorker for production.
* Additionally run behind Nginx for self-hosted deployments.
* Finally, run everything behind a CDN for caching support, and serious DDOS protection.
