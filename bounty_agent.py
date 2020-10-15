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
import logging
import socket
import time
from datetime import datetime, timedelta

import tenacity
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from skale.transactions.result import TransactionError
from web3.logs import DISCARD

from configs import (LONG_LINE, MISFIRE_GRACE_TIME, NODE_CONFIG_FILEPATH,
                     RETRY_INTERVAL)
from tools import db
from tools.exceptions import NotTimeForBountyException
from tools.helper import (MsgIcon, Notifier, call_retry,
                          check_if_node_is_registered, get_agent_name,
                          get_id_from_config, init_skale)
from tools.logger import init_agent_logger


class BountyAgent:

    def __init__(self, skale, node_id=None):
        self.agent_name = get_agent_name(self.__class__.__name__)
        init_agent_logger(self.agent_name, node_id)
        self.logger = logging.getLogger(self.agent_name)
        self.logger.info(f'Initialization of {self.agent_name} ...')
        if node_id is None:
            self.id = get_id_from_config(NODE_CONFIG_FILEPATH)
        else:
            self.id = node_id
        self.skale = skale

        check_if_node_is_registered(self.skale, self.id)

        node_info = call_retry(self.skale.nodes.get, self.id)
        self.notifier = Notifier(self.agent_name, node_info['name'],
                                 self.id, socket.inet_ntoa(node_info['ip']))
        self.is_stopped = False
        self.scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={'coalesce': True, 'misfire_grace_time': MISFIRE_GRACE_TIME})
        self.notifier.send(f'{self.agent_name} started successfully with a node ID = {self.id}',
                           icon=MsgIcon.INFO)

    def get_reward_date(self):
        try:
            reward_period = call_retry(self.skale.constants_holder.get_reward_period)
            node_info = call_retry(self.skale.nodes.get, self.id)
        except Exception as err:
            self.notifier.send(f'Cannot get reward date from SKALE Manager: {err}', MsgIcon.ERROR)
            raise
        reward_date = node_info['last_reward_date'] + reward_period
        return datetime.utcfromtimestamp(reward_date)

    def get_bounty(self):
        try:
            tx_res = self.skale.manager.get_bounty(self.id)
        except TransactionError as err:
            self.notifier.send(str(err), MsgIcon.CRITICAL)
            raise

        self.logger.debug(f'Receipt: {tx_res.receipt}')

        tx_hash = tx_res.receipt['transactionHash'].hex()
        self.logger.info(LONG_LINE)
        self.logger.info('The bounty was successfully received')

        h_receipt = self.skale.manager.contract.events.BountyReceived().processReceipt(
            tx_res.receipt, errors=DISCARD)
        self.logger.info(h_receipt)
        args = h_receipt[0]['args']
        bounty_in_skl = self.skale.web3.fromWei(args["bounty"], 'ether')
        self.notifier.send(f'Bounty awarded to node: {bounty_in_skl:.3f} SKL', MsgIcon.BOUNTY)
        try:
            db.save_bounty_event(datetime.utcfromtimestamp(args['time']), str(tx_hash),
                                 tx_res.receipt['blockNumber'], args['nodeIndex'],
                                 args['bounty'], args['averageDowntime'],
                                 args['averageLatency'], tx_res.receipt['gasUsed'])
        except Exception as err:
            self.logger.error(f'Cannot save getBounty event data to db. Error: {err}')

        return tx_res.receipt['status']

    @tenacity.retry(wait=tenacity.wait_fixed(RETRY_INTERVAL),
                    retry=tenacity.retry_if_exception_type(NotTimeForBountyException))
    def job(self) -> None:
        """Periodic job."""
        self.logger.debug('Job started')
        reward_date = self.get_reward_date()
        last_block_number = self.skale.web3.eth.blockNumber
        block_data = call_retry.call(self.skale.web3.eth.getBlock, last_block_number)
        block_timestamp = datetime.utcfromtimestamp(block_data['timestamp'])
        self.logger.info(f'Current reward time: {reward_date}')
        self.logger.info(f'Block timestamp now: {block_timestamp}')
        if reward_date > block_timestamp:
            self.logger.info('Current block timestamp is less than reward time. Will try in 1 min')
            raise NotTimeForBountyException(Exception)
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

    def stop(self):
        self.is_stopped = True
        self.scheduler.pause()


if __name__ == '__main__':
    skale = init_skale()
    bounty_agent = BountyAgent(skale)
    bounty_agent.run()
    while not bounty_agent.is_stopped:
        time.sleep(1)
        pass
