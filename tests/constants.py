""" SKALE test constants """

import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

ENDPOINT = os.environ['ENDPOINT']
HELPER_SCRIPTS_DIR = os.path.join(DIR_PATH, os.pardir, 'helper-scripts')
TEST_ABI_FILEPATH = os.path.join(HELPER_SCRIPTS_DIR, 'contracts_data', 'manager.json')
ETH_PRIVATE_KEY = os.environ['ETH_PRIVATE_KEY']

D_VALIDATOR_ID = 1
D_VALIDATOR_NAME = 'test'
D_VALIDATOR_DESC = 'test'
D_VALIDATOR_FEE = 10
D_VALIDATOR_MIN_DEL = 1000

N_TEST_NODES = 2
