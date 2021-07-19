#!/usr/bin/env bash

set -e

export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Prepare directories
sudo mkdir -p /skale_vol/contracts_info
sudo chown -R $USER:$USER /skale_vol
sudo mkdir -p /skale_node_data
sudo chown -R $USER:$USER /skale_node_data

bash ${DIR}/../helper-scripts/deploy_test_manager.sh
