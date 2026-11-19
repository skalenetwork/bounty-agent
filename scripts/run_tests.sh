#!/usr/bin/env bash

set -ea

if [ -z "${ETH_PRIVATE_KEY}" ]; then
    export ETH_PRIVATE_KEY=$(cat $PWD/helper-scripts/private_key.txt)
fi

uv run pytest -v -s --cov=./ tests/ --cov-report term-missing --cov-report xml
