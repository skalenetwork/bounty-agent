#   -*- coding: utf-8 -*-
#
#   This file is part of bounty-agent
#
#   Copyright (C) 2019-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
from enum import Enum

import redis
import requests
import tenacity
from skale import SkaleManager
from skale.utils.web3_utils import init_web3
from skale.wallets import RedisWalletAdapter, SgxWallet
from skale_core.settings import SkaleSettings

from configs import (
    CONFIG_CHECK_PERIOD,
    DEFAULT_POOL,
    NODE_CONFIG_FILEPATH,
    NOTIFIER_URL,
    REDIS_URI,
    SGX_CERTIFICATES_FOLDER,
)
from tools.exceptions import NodeNotFoundException

logger = logging.getLogger(__name__)

call_retry = tenacity.Retrying(
    stop=tenacity.stop_after_attempt(10), wait=tenacity.wait_fixed(2), reraise=True
)
_config_first_read = True


def init_skale(settings: SkaleSettings):
    wallet = init_wallet(endpoint=str(settings.endpoint), sgx_server_url=str(settings.sgx_url))
    return SkaleManager(str(settings.endpoint), settings.manager_contracts, wallet)


def init_wallet(endpoint, sgx_server_url, pool=DEFAULT_POOL):
    sgx_keyname = read_node_config('sgx_key_name')
    cpool = redis.ConnectionPool.from_url(REDIS_URI)
    rs = redis.Redis(connection_pool=cpool)
    web3 = init_web3(endpoint)
    sgx_wallet = SgxWallet(
        web3=web3,
        sgx_endpoint=sgx_server_url,
        key_name=sgx_keyname,
        path_to_cert=str(SGX_CERTIFICATES_FOLDER),
    )
    return RedisWalletAdapter(rs, pool, sgx_wallet)


def check_if_node_is_registered(skale, node_id):
    if 0 <= node_id < skale.nodes.nodes_number():
        return True
    else:
        err_msg = f'There is no Node with ID = {node_id} in SKALE manager'
        logger.error(err_msg)
        raise NodeNotFoundException(err_msg)


@tenacity.retry(
    wait=tenacity.wait_fixed(CONFIG_CHECK_PERIOD),
    retry=tenacity.retry_if_exception_type((KeyError, FileNotFoundError)),
)
def read_node_config(key: str):
    """Reads a value from the node config file, waiting until the node is registered."""
    global _config_first_read
    try:
        with open(NODE_CONFIG_FILEPATH) as json_file:
            return json.load(json_file)[key]
    except (FileNotFoundError, KeyError):
        if _config_first_read:
            logger.warning('Cannot read %s from node config - is the node already registered?', key)
            _config_first_read = False
        raise


class MsgIcon(Enum):
    INFO = '\u2705'
    WARNING = '\u26a0\ufe0f'
    ERROR = '\u203c\ufe0f'
    BOUNTY = '\U0001f4b0'
    CRITICAL = '\U0001f198'


class Notifier:
    def __init__(self, cont_name, node_name, node_id, node_ip):
        self.header = f'Container: {cont_name}, Node: {node_name}, ID: {node_id}, IP: {node_ip}\n'

    def send(self, message, icon=MsgIcon.ERROR):
        """Send message to telegram."""
        logger.info(message)
        header = f'{icon.value} {self.header}'
        message_data = {'message': [header, message]}
        try:
            response = requests.post(url=NOTIFIER_URL, json=message_data, timeout=10)
        except requests.exceptions.ConnectionError:
            logger.info(f'Cannot send Telegram notification (failed to connect to {NOTIFIER_URL})')
            return
        except Exception as err:
            logger.info(f'Cannot notify validator {NOTIFIER_URL}. {err}')
            return
        if response.status_code != requests.codes.ok:
            logger.info(f'Request to {NOTIFIER_URL} failed, status code: {response.status_code}')
            return

        res = response.json()
        if res.get('status') == 'error':
            logger.info('Telegram notifications are not supported on the node')
            return
        logger.debug('Message to validator was sent successfully')
