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

import logging
import logging.handlers as py_handlers
import os
import re
import sys
from logging import Formatter, StreamHandler
from urllib.parse import urlparse

from configs import SGX_SERVER_URL
from configs.web3 import ENDPOINT

from configs.logs import (
    LOG_BACKUP_COUNT,
    LOG_FILE_SIZE_BYTES,
    LOG_FOLDER,
    LOG_FORMAT
)


def compose_hiding_patterns():
    sgx_ip = urlparse(SGX_SERVER_URL).hostname
    eth_ip = urlparse(ENDPOINT).hostname
    return {
        rf'{sgx_ip}': '[SGX_IP]',
        rf'{eth_ip}': '[ETH_IP]',
        r'NEK\:\w+': '[SGX_KEY]'
    }


class HidingFormatter(Formatter):
    def __init__(self, log_format: str, patterns: dict) -> None:
        super().__init__(log_format)
        self._patterns: dict = patterns

    def _filter_sensitive(self, msg) -> str:
        for match, replacement in self._patterns.items():
            pat = re.compile(match)
            msg = pat.sub(replacement, msg)
        return msg

    def format(self, record) -> str:
        msg = super().format(record)
        return self._filter_sensitive(msg)

    def formatException(self, exc_info) -> str:
        msg = super().formatException(exc_info)
        return self._filter_sensitive(msg)

    def formatStack(self, stack_info) -> str:
        msg = super().formatStack(stack_info)
        return self._filter_sensitive(msg)


def create_file_handler(log_file_path):
    formatter = HidingFormatter(LOG_FORMAT, compose_hiding_patterns())
    f_handler = py_handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=LOG_FILE_SIZE_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )

    f_handler.setFormatter(formatter)
    f_handler.setLevel(logging.INFO)
    return f_handler


def create_stream_handler():
    formatter = HidingFormatter(LOG_FORMAT, compose_hiding_patterns())
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    return stream_handler


def init_logger():
    handlers = [create_stream_handler()]
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)


def init_agent_logger(agent_name, node_id):
    log_path = get_log_filepath(agent_name, node_id)
    init_logger(log_path)


def add_file_handler(logger, agent_name, node_id):
    log_path = get_log_filepath(agent_name, node_id)
    logger.addHandler(create_file_handler(log_path))


def get_log_filepath(agent_name, node_id):
    if node_id is None:  # production
        log_filename = agent_name.lower() + ".log"
    else:  # test
        log_filename = agent_name.lower() + '_' + str(node_id) + ".log"
    log_filepath = os.path.join(LOG_FOLDER, log_filename)

    return log_filepath
