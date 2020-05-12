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

import pytest

from bounty_agent import BountyCollector
from configs import NODE_CONFIG_FILEPATH
import json
from tools.exceptions import NodeNotFoundException
from tools.helper import init_skale


@pytest.fixture(scope="module")
def skale(request):
    print("\nskale setup")
    _skale = init_skale()
    return _skale


def test_init_agent(skale):
    print("Test agent init with given node id")
    agent0 = BountyCollector(skale, 0)
    assert agent0.id == 0

    print("Test agent init without given node id - read id from file")
    with open(NODE_CONFIG_FILEPATH, 'w') as json_file:
        json.dump({'node_id': 1}, json_file)

    agent1 = BountyCollector(skale)
    assert agent1.id == 1

    print("Test agent init with non-existing node id")
    with pytest.raises(NodeNotFoundException):
        BountyCollector(skale, 100)

    print("Test agent init with non-integer node id")
    with open(NODE_CONFIG_FILEPATH, 'w') as json_file:
        json.dump({'node_id': 'one'}, json_file)

    with pytest.raises(Exception):
        BountyCollector(skale)
