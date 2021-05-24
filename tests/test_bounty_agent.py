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
from skale.transactions.result import TransactionError

import bounty_agent
from configs import RETRY_INTERVAL
from tests.prepare_validator import get_active_ids, go_to_date
# from tools import db
from tools.exceptions import NodeNotFoundException
from tools.helper import check_if_node_is_registered

BLOCK_STEP = 1000


@pytest.fixture(scope="module")
def cur_node_id(skale):
    ids = get_active_ids(skale)
    return len(ids) - 2


@pytest.fixture(scope="module")
def bounty_collector(skale, cur_node_id):
    return bounty_agent.BountyAgent(skale, cur_node_id)


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

    with pytest.raises(TransactionError):
        bounty_collector.get_bounty()


def get_bounty_events(skale, cur_node_id):
    start_block_number = skale.nodes.get(cur_node_id)['start_block']  # TODO: REMOVE!!!
    # if last_block_number_in_db is None:
    #     # first_node_id = 0
    #     start_block_number = skale.nodes.get(cur_node_id)['start_block']  # TODO: REMOVE!!!
    #     # start_block_number = TEMP_LAST_BLOCK  # TODO: REMOVE!!!
    # else:
    #     # start_block_number = last_block_number_in_db + 1  # TODO: REMOVE!!!
    #     # start_block_number = max(last_block_number_in_db + 1, TEMP_LAST_BLOCK)  # TODO: REMOVE!

    while True:
        block_number = skale.web3.eth.blockNumber
        print(f'last block = {block_number}')
        end_block_number = start_block_number + BLOCK_STEP - 1
        if end_block_number > block_number:
            end_block_number = block_number
        print(f'start_block_number = {start_block_number}')
        print(f'end_block_number = {end_block_number}')
        logs = skale.manager.contract.events.BountyReceived.getLogs(
            fromBlock=hex(start_block_number),
            toBlock=hex(end_block_number))
        print('----------')
        # print(logs)
        bounty_events = []
        for log in logs:
            args = log['args']
            tx_block_number = log['blockNumber']
            block_data = skale.web3.eth.getBlock(tx_block_number)
            block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
            print(log)
            # db.save_bounty(args['nodeIndex'], args['averageLatency'], args['averageDowntime'],
            #                args['bounty'], args['gasSpend'], log['transactionHash'].hex(),
            #                log['blockNumber'], block_timestamp)
            bounty_events.append((args['nodeIndex'], args['averageLatency'],
                                  args['averageDowntime'], args['bounty'],
                                  args['gasSpend'], log['transactionHash'].hex(),
                                  log['blockNumber'], block_timestamp))

        start_block_number = start_block_number + BLOCK_STEP
        if end_block_number >= block_number:
            return bounty_events
            # break


def test_bounty_job_saves_data(skale, bounty_collector):
    # db.clear_all_bounty_receipts()
    reward_date = skale.nodes.contract.functions.getNodeNextRewardDate(bounty_collector.id).call()
    print(f'Reward date: {reward_date}')
    go_to_date(skale.web3, reward_date)
    bounty_collector.job()

    bounties = get_bounty_events(skale, bounty_collector.id)
    print(f'RESULT: {bounties}')
    print(f'LEN: {len(bounties)}')
    assert len(bounties) == 1


def test_run_agent(skale, cur_node_id):
    bounty_collector = bounty_agent.BountyAgent(skale, cur_node_id)
    reward_date = skale.nodes.contract.functions.getNodeNextRewardDate(bounty_collector.id).call()
    print(f'Reward date: {reward_date}')
    go_to_date(skale.web3, reward_date)
    # db.clear_all_bounty_receipts()

    with freeze_time(datetime.utcfromtimestamp(reward_date)):
        bounty_collector.run()
        print(f'Sleep for {RETRY_INTERVAL} sec')
        time.sleep(RETRY_INTERVAL)
        bounty_collector.stop()

    bounties = get_bounty_events(skale, bounty_collector.id)
    print(f'RESULT2: {bounties}')
    print(f'LEN2: {len(bounties)}')
    assert len(bounties) == 2
    # assert db.get_count_of_bounty_receipt_records() == 1
