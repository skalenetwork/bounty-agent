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
from tools.exceptions import NodeNotFoundException

import pytest
from skale.dataclasses.tx_res import TransactionFailedError

import bounty_agent
from tests.prepare_validator import TEST_BOUNTY_DELAY, TEST_DELTA, TEST_EPOCH, get_active_ids
from tools import db
from tools.helper import check_if_node_is_registered
from configs import RETRY_INTERVAL


@pytest.fixture(scope="module")
def cur_node_id(skale):
    ids = get_active_ids(skale)
    return len(ids) - 2


@pytest.fixture(scope="module")
def bounty_collector(skale, cur_node_id):
    print(f'\nInit Bounty collector for_node ID = {cur_node_id}')
    _bounty_collector = bounty_agent.BountyCollector(skale, cur_node_id)

    return _bounty_collector


def test_check_if_node_is_registered(skale, cur_node_id):
    assert check_if_node_is_registered(skale, cur_node_id)
    assert check_if_node_is_registered(skale, cur_node_id + 1)
    with pytest.raises(NodeNotFoundException):
        check_if_node_is_registered(skale, 100)


def test_get_bounty_neg(skale, bounty_collector):
    last_block_number = skale.web3.eth.blockNumber
    block_data = skale.web3.eth.getBlock(last_block_number)
    block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
    reward_date = bounty_collector.get_reward_date()
    print(f'Reward date: {reward_date}')
    print(f'Timestamp: {block_timestamp}')

    with pytest.raises(TransactionFailedError):
        bounty_collector.get_bounty()


def test_bounty_job_saves_data(skale, bounty_collector):
    time.sleep(TEST_EPOCH - TEST_DELTA)
    last_block_number = skale.web3.eth.blockNumber
    block_data = skale.web3.eth.getBlock(last_block_number)
    block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
    reward_date = bounty_collector.get_reward_date()
    print(f'Reward date: {reward_date}')
    print(f'Timestamp: {block_timestamp}')
    print(f'\nSleep for {TEST_DELTA} sec')
    time.sleep(TEST_DELTA + TEST_BOUNTY_DELAY)  # plus delay to wait next block after end of epoch

    db.clear_all_bounty_receipts()
    bounty_collector.job()

    assert db.get_count_of_bounty_receipt_records() == 1


def test_run_agent(skale, cur_node_id):
    last_block_number = skale.web3.eth.blockNumber
    block_data = skale.web3.eth.getBlock(last_block_number)
    block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
    db.clear_all_bounty_receipts()
    bounty_collector = bounty_agent.BountyCollector(skale, cur_node_id)
    reward_date = bounty_collector.get_reward_date()
    print(f'Reward date: {reward_date}')
    print(f'Timestamp: {block_timestamp}')

    db.clear_all_bounty_receipts()
    bounty_collector.run()
    print(f'\nSleep for {TEST_EPOCH + TEST_DELTA + RETRY_INTERVAL} sec')
    time.sleep(TEST_EPOCH + TEST_DELTA + RETRY_INTERVAL)
    bounty_collector.stop()
    assert db.get_count_of_bounty_receipt_records() == 1