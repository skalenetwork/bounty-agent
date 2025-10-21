"""SKALE config test"""

import os

import pytest
from skale import SkaleManager
from skale.utils.helper import get_skale_manager_address
from skale.utils.web3_utils import init_web3
from skale.wallets import Web3Wallet

from tests.constants import ENDPOINT, ETH_PRIVATE_KEY, N_TEST_NODES, TEST_ABI_FILEPATH
from tests.prepare_validator import create_dirs, create_set_of_nodes, get_active_ids


@pytest.fixture(scope='session', autouse=True)
def setup_test_paths():
    """Override paths for test environment"""
    os.environ['SKALE_VOLUME_PATH'] = './skale_vol'
    os.environ['NODE_DATA_PATH'] = './skale_node_data'


@pytest.fixture(scope='session')
def skale():
    """Returns a SKALE instance with provider from config"""
    web3 = init_web3(ENDPOINT)
    wallet = Web3Wallet(ETH_PRIVATE_KEY, web3)
    manager_address = get_skale_manager_address(TEST_ABI_FILEPATH)
    skale = SkaleManager(ENDPOINT, manager_address, wallet)

    create_dirs()
    ids = get_active_ids(skale)
    print(f'Existing Node IDs = {ids}')
    cur_node_id = max(ids) + 1 if len(ids) else 0
    create_set_of_nodes(skale, cur_node_id, N_TEST_NODES)
    return skale
