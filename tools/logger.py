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
import re
import sys
from logging import Formatter, StreamHandler
from urllib.parse import parse_qsl, urlparse

from configs.logs import (
    LOG_BACKUP_COUNT,
    LOG_FILE_SIZE_BYTES,
    LOG_FORMAT,
    LOG_PATH,
)

SECRET_PATH_SEGMENT_MIN_LENGTH = 16
SECRET_QUERY_VALUE_MIN_LENGTH = 12

GENERIC_HIDING_PATTERNS = {
    r'NEK\:\w+': '[SGX_KEY]',
    r'(?i)([?&](?:auth|token|apikey|api_key)=)[^&\s,\'"]+': r'\1[HIDDEN]',
}


def compose_url_hiding_patterns(url, label):
    patterns = {}
    if not url:
        return patterns
    parsed = urlparse(url)
    if parsed.query:
        patterns[re.escape(parsed.query)] = f'[{label}_QUERY]'
        for _, value in parse_qsl(parsed.query):
            if len(value) >= SECRET_QUERY_VALUE_MIN_LENGTH:
                patterns[re.escape(value)] = f'[{label}_QUERY_VALUE]'
    if parsed.password:
        patterns[re.escape(parsed.password)] = f'[{label}_PASSWORD]'
    for segment in parsed.path.split('/'):
        if len(segment) >= SECRET_PATH_SEGMENT_MIN_LENGTH:
            patterns[re.escape(segment)] = f'[{label}_PATH_SEGMENT]'
    if parsed.hostname:
        patterns[re.escape(parsed.hostname)] = f'[{label}_IP]'
    return patterns


def compose_hiding_patterns(sgx_url, endpoint):
    return {
        **compose_url_hiding_patterns(sgx_url, 'SGX'),
        **compose_url_hiding_patterns(endpoint, 'ETH'),
        **GENERIC_HIDING_PATTERNS,
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


def create_file_handler(log_file_path, sgx_url, endpoint):
    formatter = HidingFormatter(LOG_FORMAT, compose_hiding_patterns(sgx_url, endpoint))
    f_handler = py_handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=LOG_FILE_SIZE_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )

    f_handler.setFormatter(formatter)
    f_handler.setLevel(logging.INFO)
    return f_handler


def create_stream_handler(sgx_url, endpoint):
    formatter = HidingFormatter(LOG_FORMAT, compose_hiding_patterns(sgx_url, endpoint))
    stream_handler = StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    return stream_handler


def init_logger(sgx_url, endpoint):
    handlers = [
        create_file_handler(LOG_PATH, sgx_url, endpoint),
        create_stream_handler(sgx_url, endpoint),
    ]
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)
