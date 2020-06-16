import os
from skale.utils.constants import GAS

ENV = os.environ.get('ENV')

LONG_LINE = '-' * 100

NOTIFIER_URL = 'http://localhost:3007/send-tg-notification'
SKALE_VOLUME_PATH = '/skale_vol'
NODE_DATA_PATH = '/skale_node_data'

CONTRACTS_INFO_FOLDER_NAME = 'contracts_info'
MANAGER_CONTRACTS_INFO_NAME = 'manager.json'
CONTRACTS_INFO_FOLDER = os.path.join(SKALE_VOLUME_PATH, CONTRACTS_INFO_FOLDER_NAME)
NODE_CONFIG_FILENAME = 'node_config.json'
NODE_CONFIG_FILEPATH = os.path.join(NODE_DATA_PATH, NODE_CONFIG_FILENAME)

MIN_ETH_AMOUNT_IN_SKL = 0.01
MIN_ETH_AMOUNT = int(MIN_ETH_AMOUNT_IN_SKL * (10 ** 18))
BLOCK_STEP_SIZE = 2000
RETRY_INTERVAL = 60
MISFIRE_GRACE_TIME = 365 * 24 * 60 * 60
GAS_LIMIT = GAS['get_bounty']
