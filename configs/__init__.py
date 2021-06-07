import os

ENV = os.environ.get('ENV')

LONG_LINE = '-' * 100

NOTIFIER_URL = 'http://localhost:3007/send-tg-notification'
SKALE_VOLUME_PATH = '/skale_vol'
NODE_DATA_PATH = '/skale_node_data'

CONTRACTS_INFO_FOLDER_NAME = 'contracts_info'
MANAGER_CONTRACTS_INFO_NAME = 'manager.json'
CONTRACTS_INFO_FOLDER = os.path.join(SKALE_VOLUME_PATH,
                                     CONTRACTS_INFO_FOLDER_NAME)
NODE_CONFIG_FILENAME = 'node_config.json'
NODE_CONFIG_FILEPATH = os.path.join(NODE_DATA_PATH, NODE_CONFIG_FILENAME)

STATE_FILENAME = os.getenv('STATE_FILENAME')
STATE_BASE_PATH = os.path.join(NODE_DATA_PATH, 'eth-state')
STATE_FILEPATH = None if not STATE_FILENAME \
                    else os.path.join(STATE_BASE_PATH, STATE_FILENAME)

MIN_ETH_AMOUNT_IN_SKL = 0.01
MIN_ETH_AMOUNT = int(MIN_ETH_AMOUNT_IN_SKL * (10 ** 18))
RETRY_INTERVAL = 60  # in seconds
CONFIG_CHECK_PERIOD = 30  # in seconds
MISFIRE_GRACE_TIME = 365 * 24 * 60 * 60  # in seconds
DELAY_AFTER_ERR = 60  # in seconds

SGX_SERVER_URL = os.getenv('SGX_SERVER_URL')
SGX_CERTIFICATES_FOLDER_NAME = os.getenv('SGX_CERTIFICATES_DIR_NAME')

if SGX_CERTIFICATES_FOLDER_NAME:
    SGX_CERTIFICATES_FOLDER = os.path.join(
        NODE_DATA_PATH,
        SGX_CERTIFICATES_FOLDER_NAME
    )
else:
    SGX_CERTIFICATES_FOLDER = os.getenv('SGX_CERTIFICATES_FOLDER')

DEFAULT_POOL = 'transactions'
REDIS_URI = os.getenv('REDIS_URI', 'redis://@127.0.0.1:6379')
