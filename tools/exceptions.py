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


class NotTimeForBountyException(Exception):
    """Raised when reward date has come but current block's timestamp is less than reward date."""


class NodeNotFoundException(Exception):
    """Raised when Node ID doesn't exist in SKALE Manager."""


class NotEnoughEthForTxException(Exception):
    """Raised when a wallet balance is too low to send a transaction."""
