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
import re
from enum import Enum

import redis
import requests
import tenacity
from skale import Skale
from skale.utils.web3_utils import init_web3
from skale.wallets import RedisWalletAdapter, SgxWallet

from configs import (
    CONFIG_CHECK_PERIOD,
    DEFAULT_POOL,
    NOTIFIER_URL,
    NODE_CONFIG_FILEPATH,
    REDIS_URI,
    SGX_CERTIFICATES_FOLDER,
    SGX_SERVER_URL,
    STATE_FILEPATH
)
from configs.web3 import ABI_FILEPATH, ENDPOINT
from tools.exceptions import NodeNotFoundException

logger = logging.getLogger(__name__)

call_retry = tenacity.Retrying(stop=tenacity.stop_after_attempt(10),
                               wait=tenacity.wait_fixed(2),
                               reraise=True)
_config_first_read = True


def init_skale():
    wallet = init_wallet()
    return Skale(ENDPOINT, ABI_FILEPATH, wallet, state_path=STATE_FILEPATH)


def init_wallet(pool=DEFAULT_POOL):
    sgx_keyname = get_sgx_keyname_from_config(NODE_CONFIG_FILEPATH)
    cpool = redis.ConnectionPool.from_url(REDIS_URI)
    rs = redis.Redis(connection_pool=cpool)
    web3 = init_web3(ENDPOINT)
    sgx_wallet = SgxWallet(
        web3=web3,
        sgx_endpoint=SGX_SERVER_URL,
        key_name=sgx_keyname,
        path_to_cert=SGX_CERTIFICATES_FOLDER
    )
    return RedisWalletAdapter(rs, pool, sgx_wallet)


def get_agent_name(name):
    name_parts = re.findall('[A-Z][^A-Z]*', name)
    return '-'.join(name_parts).lower()


def check_if_node_is_registered(skale, node_id):
    if 0 <= node_id < skale.nodes.get_nodes_number():
        return True
    else:
        err_msg = f'There is no Node with ID = {node_id} in SKALE manager'
        logger.error(err_msg)
        raise NodeNotFoundException(err_msg)


@tenacity.retry(
    wait=tenacity.wait_fixed(CONFIG_CHECK_PERIOD),
    retry=tenacity.retry_if_exception_type(KeyError) | tenacity.retry_if_exception_type(
        FileNotFoundError))
def get_id_from_config(node_config_filepath) -> int:
    """Gets node ID from config file for agent initialization."""
    global _config_first_read
    try:
        logger.debug('Reading node id from config file...')
        with open(node_config_filepath) as json_file:
            data = json.load(json_file)
        return data['node_id']
    except (FileNotFoundError, KeyError) as err:
        if _config_first_read:
            logger.warning(
                'Cannot read a node id from config file - is the node already registered?')
            _config_first_read = False
        raise err


@tenacity.retry(
    wait=tenacity.wait_fixed(CONFIG_CHECK_PERIOD),
    retry=tenacity.retry_if_exception_type(KeyError) | tenacity.retry_if_exception_type(
        FileNotFoundError))
def get_sgx_keyname_from_config(node_config_filepath) -> int:
    """Gets sgx keyname from config file."""
    global _config_first_read
    try:
        logger.debug('Reading node id from config file...')
        with open(node_config_filepath) as json_file:
            data = json.load(json_file)
        return data['sgx_key_name']
    except (FileNotFoundError, KeyError) as err:
        if _config_first_read:
            logger.warning(
                'Cannot read a sgx_key_name from config file?')
            _config_first_read = False
        raise err


class MsgIcon(Enum):
    INFO = '\u2705'
    WARNING = '\u26a0\ufe0f'
    ERROR = '\u203c\ufe0f'
    BOUNTY = '\ud83d\udcb0'
    CRITICAL = '\ud83c\udd98'


class Notifier:
    def __init__(self, cont_name, node_name, node_id, node_ip):
        self.header = f'Container: {cont_name}, Node: {node_name}, ' \
                      f'ID: {node_id}, IP: {node_ip}\n'

    def send(self, message, icon=MsgIcon.ERROR):
        """Send message to telegram."""
        logger.info(message)
        header = f'{icon.value} {self.header}'
        message_data = {"message": [header, message]}
        try:
            response = requests.post(url=NOTIFIER_URL, json=message_data)
        except requests.exceptions.ConnectionError:
            logger.info(f'Cannot send Telegram notification (failed to connect to {NOTIFIER_URL})')
            return 1
        except Exception as err:
            logger.info(f'Cannot notify validator {NOTIFIER_URL}. {err}')
            return 1
        if response.status_code != requests.codes.ok:
            logger.info(f'Request to {NOTIFIER_URL} failed, status code: {response.status_code}')
            return 1

        res = response.json()
        if res.get('status') == 'error':
            logger.info('Telegram notifications are not supported on the node')
            return 1
        logger.debug('Message to validator was sent successfully')
        return 0
