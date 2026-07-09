#!/bin/bash

DBFILE="../../prundb/prundb.db"

if [[ ! -f "$DBFILE" ]]; then
	echo "dbfile not found at $DBFILE. please touch that file and rerun this script"
	exit 1
fi

sqlite3 $DBFILE < schema.sql

# setup venv
if [[ ! -d ".venv" ]]; then
	python3 -m venv .venv || exit 1
fi

if [[ ! -e "$VIRTUAL_ENV" ]]; then
	source .venv/bin/activate || exit 1
fi

# install python packages
pip install -r requirements.txt
