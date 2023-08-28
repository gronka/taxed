#!/bin/sh

echo you can run this like for debugging
echo ./run-biller.sh day=1 period=202203

cd bills

export DB_CHOICE=postgresql
export TAXED_ENV=local
export TAXED_ROOT=/taxed/taxed

/usr/bin/env python3 run_biller.py $@
