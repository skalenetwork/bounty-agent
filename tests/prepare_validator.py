import os
from datetime import datetime

from skale import Skale
from skale.utils.web3_utils import init_web3
from skale.wallets import Web3Wallet
from skale.utils.contracts_provision.main import add_test_permissions


from tests.constants import (D_VALIDATOR_DESC, D_VALIDATOR_FEE, D_VALIDATOR_ID,
                             D_VALIDATOR_MIN_DEL, D_VALIDATOR_NAME, ENDPOINT,
                             ETH_PRIVATE_KEY, TEST_ABI_FILEPATH)

IP_BASE = '10.1.0.'
TEST_PORT = 123
DIR_LOG = '/skale_node_data/log'
DIR_ABI = '/skale_vol/contracts_info'


def create_dirs():
    if not os.path.exists(DIR_LOG):
        os.makedirs(DIR_LOG)
    if not os.path.exists(DIR_ABI):
        os.makedirs(DIR_ABI)


def validator_exist(skale):
    return skale.validator_service.number_of_validators() > 0


def setup_validator(skale):
    """Create and activate a validator"""
    add_test_permissions(skale)
    if not validator_exist(skale):
        create_validator(skale)
        enable_validator(skale)
    set_test_msr(skale, msr=0)


def get_block_timestamp(web3):
    last_block_number = web3.eth.blockNumber
    block_data = web3.eth.getBlock(last_block_number)
    return block_data['timestamp']


def go_to_date(web3, date):
    block_timestamp = get_block_timestamp(web3)
    print(f'Block timestamp before: {datetime.utcfromtimestamp(block_timestamp)}')
    delta = date - block_timestamp

    skip_evm_time(web3, delta)

    block_timestamp = get_block_timestamp(web3)
    print(f'Block timestamp after: {datetime.utcfromtimestamp(block_timestamp)}')


def set_test_msr(skale, msr=D_VALIDATOR_MIN_DEL):
    skale.constants_holder._set_msr(
        new_msr=msr,
        wait_for=True
    )


def enable_validator(skale):
    print(f'Enabling validator ID: {D_VALIDATOR_ID}')
    skale.validator_service._enable_validator(D_VALIDATOR_ID, wait_for=True)


def create_validator(skale):
    print('Creating default validator')
    skale.validator_service.register_validator(
        name=D_VALIDATOR_NAME,
        description=D_VALIDATOR_DESC,
        fee_rate=D_VALIDATOR_FEE,
        min_delegation_amount=D_VALIDATOR_MIN_DEL,
        wait_for=True
    )


def create_node(skale, node_id):
    name = f'node_{node_id}'
    ip = f'{IP_BASE}{node_id}'
    domain_name = f'skalebounty{node_id}.com'
    res_tx = skale.manager.create_node(
        ip, TEST_PORT, name, domain_name, wait_for=True)

    if res_tx.receipt['status'] == 1:
        print(f'Node with ID={node_id} was successfully created')
    else:
        print(f'Failed to create - Node ID={node_id}')
        print(res_tx.receipt)


def get_active_ids(skale):
    return skale.nodes.get_active_node_ids()


def create_set_of_nodes(skale, first_node_id, nodes_number=2):

    active_ids = get_active_ids(skale)
    print(active_ids)

    if first_node_id not in active_ids:

        print(f'Starting creating {nodes_number} nodes from id = {first_node_id}:')
        for node_id in range(first_node_id, first_node_id + nodes_number):
            print(f'Creating node with id = {node_id}')
            create_node(skale, node_id)
    else:
        print(f'Node with id = {first_node_id} is already exists! Try another start id...')


def skip_evm_time(web3, seconds) -> int:
    """For test purposes only, works only with ganache node"""
    res = web3.provider.make_request("evm_increaseTime", [seconds])
    web3.provider.make_request("evm_mine", [])
    return res['result']


def init_skale():
    web3 = init_web3(ENDPOINT)
    wallet = Web3Wallet(ETH_PRIVATE_KEY, web3)
    return Skale(ENDPOINT, TEST_ABI_FILEPATH, wallet)


if __name__ == "__main__":
    skale = init_skale()
    setup_validator(skale)
