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

import redis
import tenacity
from skale import SkaleManager
from skale.utils.web3_utils import init_web3
from skale.wallets import RedisWalletAdapter, SgxWallet
from skale_core.settings import SkaleSettings

from configs import (
    CONFIG_CHECK_PERIOD,
    DEFAULT_POOL,
    NODE_CONFIG_FILEPATH,
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
