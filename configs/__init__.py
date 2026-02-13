import os
from pathlib import Path
from skale.core.settings import (
    SkaleSettings,
)

ENV = os.environ.get('ENV')

LONG_LINE = '-' * 100

NOTIFIER_URL = 'http://localhost:3007/send-tg-notification'
NODE_DATA_FOLDER_NAME: str = 'node_data'

SKALE_VOLUME_PATH: Path = Path(os.getenv('SKALE_VOLUME_PATH', '/skale_vol'))
NODE_DATA_PATH: Path = SKALE_VOLUME_PATH / NODE_DATA_FOLDER_NAME

NODE_CONFIG_FILENAME = 'node_config.json'
NODE_CONFIG_FILEPATH: Path = NODE_DATA_PATH / NODE_CONFIG_FILENAME

MIN_ETH_AMOUNT_IN_SKL = 0.01
MIN_ETH_AMOUNT = int(MIN_ETH_AMOUNT_IN_SKL * (10**18))
RETRY_INTERVAL = 60  # in seconds
CONFIG_CHECK_PERIOD = 30  # in seconds
MISFIRE_GRACE_TIME = 365 * 24 * 60 * 60  # in seconds
DELAY_AFTER_ERR = 60  # in seconds

SGX_CERTIFICATES_FOLDER = NODE_DATA_PATH / 'sgx_certs'

DEFAULT_POOL = 'transactions'
REDIS_URI = os.getenv('REDIS_URI', 'redis://@127.0.0.1:6379')

SETTINGS_FOLDER_PATH: Path = SKALE_VOLUME_PATH / 'settings'
NODE_SETTINGS_PATH: Path = SETTINGS_FOLDER_PATH / 'node.toml'
SkaleSettings.model_config['toml_file'] = NODE_SETTINGS_PATH