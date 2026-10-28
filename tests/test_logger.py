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

from tools.logger import create_file_handler, create_stream_handler

SGX_URL = 'https://10.0.0.1:1026'
ENDPOINT = 'http://10.0.0.2:8545'


def test_handlers_hide_sensitive_data(tmp_path, capsys):
    log_path = tmp_path / 'bounty-agent.log'
    logger = logging.getLogger('test-logger')
    logger.addHandler(create_file_handler(log_path, SGX_URL, ENDPOINT))
    logger.addHandler(create_stream_handler(SGX_URL, ENDPOINT))

    try:
        raise ValueError('SGX at 10.0.0.1 failed')
    except ValueError:
        logger.exception('Endpoint 10.0.0.2, key NEK:abc123', stack_info=True)

    for output in (log_path.read_text(), capsys.readouterr().err):
        assert '[SGX_IP]' in output and '[ETH_IP]' in output and '[SGX_KEY]' in output
        assert '10.0.0.1' not in output and '10.0.0.2' not in output
        assert 'NEK:abc123' not in output
