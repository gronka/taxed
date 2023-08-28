#!/bin/sh

cd deployment/database/
./startDb.sh

cd ../../src/taxed

export TAXED_ENV=local
export TAXED_ROOT=/taxed/taxed
#uvicorn asgi:app --reload --host 0.0.0.0
uvicorn asgi:app \
	--reload \
	--forwarded-allow-ips='*' \
	--uds /taxed/tmp/taxed.uvicorn.sock \
	--proxy-headers 
