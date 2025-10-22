export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

export ENDPOINT=http://127.0.0.1:8545
export MANAGER_TAG=1.12.0-develop.23
export RUN_ANVIL=true
export SKALE_VOLUME_PATH=$DIR/../skale_vol
export NODE_DATA_PATH=$DIR/../skale_node_data
export PYTHONPATH=$PYTHONPATH:.
export ALLOWED_TS_DIFF=-1
