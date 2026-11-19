"""SKALE config test"""

import pytest
from skale import SkaleManager
from skale.utils.helper import get_skale_manager_address
from skale.utils.web3_utils import init_web3
from skale.wallets import Web3Wallet

from configs import NODE_DATA_PATH
from tests.constants import ENDPOINT, ETH_PRIVATE_KEY, N_TEST_NODES, TEST_ABI_FILEPATH
from tests.prepare_validator import create_set_of_nodes, get_active_ids, setup_validator


@pytest.fixture(scope='session', autouse=True)
def node_data_dir():
    NODE_DATA_PATH.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope='session')
def skale():
    """Returns a SKALE instance with provider from config"""
    wallet = Web3Wallet(ETH_PRIVATE_KEY, init_web3(ENDPOINT))
    skale = SkaleManager(ENDPOINT, get_skale_manager_address(TEST_ABI_FILEPATH), wallet)

    setup_validator(skale)

    ids = get_active_ids(skale)
    print(f'Existing Node IDs = {ids}')
    cur_node_id = max(ids) + 1 if len(ids) else 0
    create_set_of_nodes(skale, cur_node_id, N_TEST_NODES)
    return skale
