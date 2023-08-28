#!/bin/sh

cd src/taxed

export TAXED_ENV=prod
export TAXED_ROOT=/taxed/taxed
#uvicorn asgi:app --reload --host 0.0.0.0
uvicorn asgi:app \
	--reload \
	--uds /taxed/tmp/taxed.uvicorn.sock \
	--forwarded-allow-ips='*' \
	--proxy-headers 
