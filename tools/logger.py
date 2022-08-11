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

import hashlib
import logging
import logging.handlers as py_handlers
import os
import re
import sys
from logging import Formatter, StreamHandler

from configs.logs import (LOG_BACKUP_COUNT, LOG_FILE_SIZE_BYTES, LOG_FOLDER,
                          LOG_FORMAT)

HIDING_PATTERNS = [
    r'NEK\:\w+',
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    r'ws[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'  # noqa
]


class HidingFormatter:
    def __init__(self, base_formatter, patterns):
        self.base_formatter = base_formatter
        self._patterns = patterns

    @classmethod
    def convert_match_to_sha3(cls, match):
        return hashlib.sha3_256(match.group(0).encode('utf-8')).digest().hex()

    def format(self, record):
        msg = self.base_formatter.format(record)
        for pattern in self._patterns:
            pat = re.compile(pattern)
            msg = pat.sub(self.convert_match_to_sha3, msg)
        return msg

    def __getattr__(self, attr):
        return getattr(self.base_formatter, attr)


def init_logger(log_file_path):
    handlers = []

    base_formatter = Formatter(LOG_FORMAT)
    formatter = HidingFormatter(base_formatter, HIDING_PATTERNS)

    f_handler = py_handlers.RotatingFileHandler(log_file_path,
                                                maxBytes=LOG_FILE_SIZE_BYTES,
                                                backupCount=LOG_BACKUP_COUNT)

    f_handler.setFormatter(formatter)
    f_handler.setLevel(logging.INFO)
    handlers.append(f_handler)

    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    handlers.append(stream_handler)

    logging.basicConfig(level=logging.DEBUG, handlers=handlers)


def init_agent_logger(agent_name, node_id):
    log_path = get_log_filepath(agent_name, node_id)
    init_logger(log_path)


def get_log_filepath(agent_name, node_id):
    if node_id is None:  # production
        log_filename = agent_name.lower() + ".log"
    else:  # test
        log_filename = agent_name.lower() + '_' + str(node_id) + ".log"
    log_filepath = os.path.join(LOG_FOLDER, log_filename)

    return log_filepath
