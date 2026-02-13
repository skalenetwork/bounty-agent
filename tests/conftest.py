"""SKALE config test"""

import os

import pytest
from skale import SkaleManager
from skale.core.settings import SkaleSettings
from skale.utils.helper import get_skale_manager_address
from skale.utils.web3_utils import init_web3
from skale.wallets import Web3Wallet

from tests.constants import ENDPOINT, ETH_PRIVATE_KEY, N_TEST_NODES, TEST_ABI_FILEPATH
from tests.prepare_validator import (
    create_dirs,
    create_set_of_nodes,
    get_active_ids,
    setup_validator,
)


@pytest.fixture(scope='session', autouse=True)
def setup_test_paths():
    """Override paths for test environment"""
    os.environ['SKALE_VOLUME_PATH'] = './skale_vol'
    os.environ['NODE_DATA_PATH'] = './skale_node_data'

    # Force low gas price for tests to avoid Insufficient Funds in local anvil
    import skale.config as skale_config
    skale_config.DEFAULT_GAS_PRICE = 1000000000  # 1 Gwei


@pytest.fixture(scope='session')
def settings():
    # Set fake defaults for tests to pass Pydantic validation
    defaults = {
        'ENV_TYPE': 'devnet',
        'NODE_VERSION': '0.0.0',
        'BLOCK_DEVICE': '/dev/sda',
        'MANAGER_CONTRACTS': '0x' + '0' * 40,
        'IMA_CONTRACTS': '0x' + '0' * 40,
        'DOCKER_LVMPY_VERSION': '0.0.0',
        'DOCKER_IMAGE': 'skalenetwork/skale-node:0.0.0',
        'SGX_URL': 'http://localhost:1026',
        'SGX_SERVER_URL': 'http://localhost:1026',
        'DEFAULT_GAS_PRICE_WEI': '1000000000',  # 1 Gwei string for env var
    }

    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = str(value)

    return SkaleSettings()


@pytest.fixture(scope='session')
def skale():
    """Returns a SKALE instance with provider from config"""
    web3 = init_web3(ENDPOINT)
    wallet = Web3Wallet(ETH_PRIVATE_KEY, web3)
    manager_address = get_skale_manager_address(TEST_ABI_FILEPATH)
    skale = SkaleManager(ENDPOINT, manager_address, wallet)

    create_dirs()

    setup_validator(skale)

    ids = get_active_ids(skale)
    print(f'Existing Node IDs = {ids}')
    cur_node_id = max(ids) + 1 if len(ids) else 0
    create_set_of_nodes(skale, cur_node_id, N_TEST_NODES)
    return skale
