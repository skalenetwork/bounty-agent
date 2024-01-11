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

import time
from datetime import datetime

import pytest
from freezegun import freeze_time
from skale.transactions.exceptions import TransactionError

import bounty_agent
from tests.prepare_validator import get_active_ids, go_to_date
from tools.exceptions import NodeNotFoundException
from tools.helper import check_if_node_is_registered

MINING_DELAY = 5
REWARD_DATE_OFFSET = 10  # additional seconds to skip to ensure reward time is came


@pytest.fixture(scope="module")
def node_id(skale):
    ids = get_active_ids(skale)
    return len(ids) - 2


@pytest.fixture(scope="module")
def bounty_collector(skale, node_id):
    return bounty_agent.BountyAgent(skale, node_id)


def test_check_if_node_is_registered(skale, node_id):
    assert check_if_node_is_registered(skale, node_id)
    assert check_if_node_is_registered(skale, node_id + 1)
    with pytest.raises(NodeNotFoundException):
        check_if_node_is_registered(skale, 100)


def test_get_bounty_neg(skale, bounty_collector):
    last_block_number = skale.web3.eth.block_number
    block_data = skale.web3.eth.get_block(last_block_number)
    block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
    reward_date = bounty_collector.get_reward_date()
    print(f'Reward date: {reward_date}')
    print(f'Timestamp: {block_timestamp}')

    with pytest.raises(TransactionError):
        bounty_collector.get_bounty()


def get_bounty_events(skale, node_id):
    from_block_number = skale.nodes.get(node_id)['start_block']
    to_block_number = skale.web3.eth.block_number
    logs = skale.manager.contract.events.BountyReceived.get_logs(
        fromBlock=hex(from_block_number),
        toBlock=hex(to_block_number))
    bounty_events = []
    for log in logs:
        args = log['args']
        tx_block_number = log['blockNumber']
        block_data = skale.web3.eth.get_block(tx_block_number)
        block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
        bounty_events.append((args['nodeIndex'], args['averageLatency'],
                              args['averageDowntime'], args['bounty'],
                              log['transactionHash'].hex(),
                              log['blockNumber'], block_timestamp))
    return bounty_events


def test_bounty_job_saves_data(skale, bounty_collector):
    reward_date = skale.nodes.contract.functions.getNodeNextRewardDate(bounty_collector.id).call()
    print(f'Reward date: {reward_date}')
    go_to_date(skale.web3, reward_date + REWARD_DATE_OFFSET)
    print('Latest block timestamp', skale.web3.eth.get_block('latest')['timestamp'])
    bounty_collector.job()
    time.sleep(MINING_DELAY)

    bounties = get_bounty_events(skale, bounty_collector.id)
    assert len(bounties) == 1


def test_run_agent(skale, node_id):
    bounty_collector = bounty_agent.BountyAgent(skale, node_id)
    reward_date = skale.nodes.contract.functions.getNodeNextRewardDate(bounty_collector.id).call()
    print(f'Reward date: {reward_date}')
    go_to_date(skale.web3, reward_date + REWARD_DATE_OFFSET)
    print('Latest block timestamp', skale.web3.eth.get_block('latest')['timestamp'])

    with freeze_time(datetime.utcfromtimestamp(reward_date + REWARD_DATE_OFFSET)):
        bounty_collector.run()
        bounty_collector.stop()

    time.sleep(MINING_DELAY)
    bounties = get_bounty_events(skale, bounty_collector.id)
    assert len(bounties) == 2
