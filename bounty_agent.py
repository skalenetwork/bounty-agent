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

"""
Bounty agent runs on every node of SKALE network.
Agent requests to receive available reward for validation work.
"""
import sys
import time
from datetime import datetime, timedelta

import tenacity
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from web3.logs import DISCARD
from configs import (BLOCK_STEP_SIZE, LONG_LINE, MISFIRE_GRACE_TIME,
                     NODE_CONFIG_FILEPATH)
from tools import db
from tools.exceptions import IsNotTimeException, TxCallFailedException
from tools.helper import (
    call_tx_retry, check_if_node_is_registered, get_id_from_config, init_skale, regular_call_retry,
    send_tx_retry)
from tools.logger import init_agent_logger
import logging


class BountyCollector:

    def __init__(self, skale, node_id=None):
        self.agent_name = self.__class__.__name__.lower()
        init_agent_logger(self.agent_name, node_id)
        self.logger = logging.getLogger(self.agent_name)

        self.logger.info(f'Initialization of {self.agent_name} ...')
        if node_id is None:
            self.id = get_id_from_config(NODE_CONFIG_FILEPATH)
            self.is_test_mode = False
        else:
            self.id = node_id
            self.is_test_mode = True
        self.skale = skale

        check_if_node_is_registered(self.skale, self.id)

        self.logger.info('Check logs on blockchain')
        start = time.time()
        try:
            self.collect_last_bounty_logs()
        except Exception as err:
            self.logger.error(f'Error occurred while checking logs from blockchain: {err} ')
            # TODO: notify SKALE Admin
        end = time.time()
        self.logger.info(f'Check completed. Execution time = {end - start}')
        self.scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={'coalesce': True, 'misfire_grace_time': MISFIRE_GRACE_TIME})
        self.logger.info(f'Initialization of {self.agent_name} is completed. Node ID = {self.id}')

    def get_reward_date(self):
        reward_period = regular_call_retry(self.skale.constants_holder.get_reward_period)
        node_info = regular_call_retry(self.skale.nodes_data.get, self.id)
        reward_date = node_info['last_reward_date'] + reward_period
        return datetime.utcfromtimestamp(reward_date)

    def collect_last_bounty_logs(self):
        start_block_number = self.skale.nodes_data.get(self.id)['start_block']
        last_block_number_in_db = db.get_bounty_max_block_number()
        if last_block_number_in_db is not None:
            start_block_number = last_block_number_in_db + 1
        count = 0
        while True:
            last_block_number = self.skale.web3.eth.blockNumber
            self.logger.debug(f'last block = {last_block_number}')
            end_chunk_block_number = start_block_number + BLOCK_STEP_SIZE - 1

            if end_chunk_block_number > last_block_number:
                end_chunk_block_number = last_block_number + 1
            event_filter = self.skale.manager.contract.events.BountyGot.createFilter(
                argument_filters={'nodeIndex': self.id},
                fromBlock=hex(start_block_number),
                toBlock=hex(end_chunk_block_number))
            logs = event_filter.get_all_entries()

            for log in logs:
                args = log['args']
                tx_block_number = log['blockNumber']
                block_data = self.skale.web3.eth.getBlock(tx_block_number)
                block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
                self.logger.debug(log)
                tx_hash = log['transactionHash'].hex()
                gas_used = self.skale.web3.eth.getTransactionReceipt(tx_hash)['gasUsed']
                db.save_bounty_event(block_timestamp, tx_hash,
                                     log['blockNumber'], args['nodeIndex'], args['bounty'],
                                     args['averageDowntime'], args['averageLatency'],
                                     gas_used)
                count += 1
            self.logger.debug(f'Iterations count = {count}')
            start_block_number = start_block_number + BLOCK_STEP_SIZE
            if end_chunk_block_number >= last_block_number:
                break

    def get_bounty(self):
        address = self.skale.wallet.address
        eth_bal_before = self.skale.web3.eth.getBalance(address)
        self.logger.info(f'ETH balance: {self.skale.web3.fromWei(eth_bal_before, "ether")}')

        call_tx_retry.call(self.skale.manager.get_bounty, self.id, dry_run=True)
        tx_res = send_tx_retry.call(self.skale.manager.get_bounty, self.id, wait_for=True)
        self.logger.debug(f'Receipt: {tx_res.receipt}')
        tx_res.raise_for_status()

        tx_hash = tx_res.receipt['transactionHash'].hex()
        self.logger.info(LONG_LINE)
        self.logger.info('The bounty was successfully received')

        eth_bal = self.skale.web3.eth.getBalance(address)
        self.logger.debug(f'ETH spend: {eth_bal_before - eth_bal}')

        h_receipt = self.skale.manager.contract.events.BountyGot().processReceipt(
            tx_res.receipt, errors=DISCARD)
        self.logger.info(h_receipt)
        args = h_receipt[0]['args']
        try:
            db.save_bounty_event(datetime.utcfromtimestamp(args['time']), str(tx_hash),
                                 tx_res.receipt['blockNumber'], args['nodeIndex'],
                                 args['bounty'], args['averageDowntime'],
                                 args['averageLatency'], tx_res.receipt['gasUsed'])
        except Exception as err:
            self.logger.error(f'Cannot save getBounty event data to db. Error: {err}')

        return tx_res.receipt['status']

    @tenacity.retry(wait=tenacity.wait_fixed(60),
                    retry=tenacity.retry_if_exception_type(IsNotTimeException) | tenacity.
                    retry_if_exception_type(TxCallFailedException))
    def job(self) -> None:
        """Periodic job."""
        self.logger.debug(f'Job started')

        try:
            reward_date = self.get_reward_date()
        except Exception as err:
            self.logger.error(f'Cannot get reward date from SKALE Manager: {err}')
            # TODO: notify SKALE Admin
            raise

        last_block_number = self.skale.web3.eth.blockNumber
        block_data = regular_call_retry.call(self.skale.web3.eth.getBlock, last_block_number)
        block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
        self.logger.info(f'Current reward time: {reward_date}')
        self.logger.info(f'Block timestamp now: {block_timestamp}')
        if reward_date > block_timestamp:
            self.logger.info('Current block timestamp is less than reward time. Will try in 1 min')
            raise IsNotTimeException(Exception)
        self.get_bounty()

    def job_listener(self, event):
        if event.exception:
            self.logger.info('The job failed')
            utc_now = datetime.utcnow()
            self.scheduler.add_job(self.job, 'date', run_date=utc_now + timedelta(seconds=60))
            self.logger.debug(self.scheduler.get_jobs())
        else:
            self.logger.debug('The job finished successfully)')
            reward_date = self.get_reward_date()
            self.logger.debug(f'Reward date after job: {reward_date}')
            utc_now = datetime.utcnow()
            if utc_now > reward_date:
                self.logger.debug('Changing reward time by current time')
                reward_date = utc_now
            self.scheduler.add_job(self.job, 'date', run_date=reward_date)
            self.scheduler.print_jobs()

    def run(self) -> None:
        """Starts agent."""
        reward_date = self.get_reward_date()
        self.logger.debug(f'Reward date on agent\'s start: {reward_date}')
        utc_now = datetime.utcnow()
        if utc_now > reward_date:
            reward_date = utc_now
        self.scheduler.add_job(self.job, 'date', run_date=reward_date)
        self.scheduler.print_jobs()
        self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()
        while True:
            time.sleep(1)
            pass


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].isdecimal():
        node_id = int(sys.argv[1])
    else:
        node_id = None

    skale = init_skale(node_id)
    bounty_agent = BountyCollector(skale, node_id)
    bounty_agent.run()
