#!/usr/bin/env bash

set -ea

export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Prepare directories
mkdir -p $DIR/../skale_vol/contracts_info
mkdir -p $DIR/../skale_node_data

if [ -z "${ETH_PRIVATE_KEY}" ]; then
    export ETH_PRIVATE_KEY=$(cat $PWD/helper-scripts/private_key.txt)
fi

python tests/prepare_validator.py
ENV=DEV pytest -v -s --cov=./ tests/ --cov-report term-missing