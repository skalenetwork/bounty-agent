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


from configs.db import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from peewee import CharField, DateTimeField, IntegerField, Model, MySQLDatabase, fn

db = MySQLDatabase(
    DB_NAME, user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)


class BaseModel(Model):
    class Meta:
        database = db


class BountyEvent(BaseModel):
    my_id = IntegerField()
    tx_dt = DateTimeField()
    tx_hash = CharField()
    block_number = IntegerField()
    bounty = CharField()
    downtime = IntegerField()
    latency = IntegerField()
    gas_used = IntegerField()

    class Meta:
        table_name = 'bounty_event'


@db.connection_context()
def save_bounty_event(tx_dt, tx_hash, block_number, my_id, bounty, downtime, latency, gas_used):
    """Save bounty events data to database."""
    data = BountyEvent(my_id=my_id,
                       tx_dt=tx_dt,
                       bounty=bounty,
                       downtime=downtime,
                       latency=latency,
                       gas_used=gas_used,
                       tx_hash=tx_hash,
                       block_number=block_number)

    data.save()


@db.connection_context()
def clear_all_bounty_receipts():
    nrows = BountyEvent.delete().execute()
    print(f'{nrows} records deleted')


@db.connection_context()
def get_count_of_bounty_receipt_records():
    return BountyEvent.select().count()


@db.connection_context()
def get_bounty_max_block_number():
    return BountyEvent.select(fn.MAX(BountyEvent.block_number)).scalar()
