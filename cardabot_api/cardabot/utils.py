"""Helper functions for the cardabot endpoints."""

import os
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler
from blockfrost import ApiError, ApiUrls, BlockFrostApi


@dataclass
class BlockFrostAPI:
    base_url = (
        ApiUrls.testnet.value
        if os.environ["NETWORK"] == "testnet"
        else ApiUrls.mainnet.value
    )
    api = BlockFrostApi(project_id=os.environ.get("BLOCKFROST_ID"), base_url=base_url)


class Scheduler:
    queue = BackgroundScheduler()
    queue.start()  # start scheduler


def lovelace_to_ada(lovelace_value: int) -> float:
    """Take a value in lovelace and return it in ADA."""
    constant = 1e6
    return int(lovelace_value) / constant


def values_to_ada(values: list[int], currency: str) -> list:
    """Convert a list of lovelace values to ADA if needed."""
    if currency and currency.upper() == "ADA":
        values = [lovelace_to_ada(value) for value in values]
        return values

    return [int(value) for value in values]  # keep values in lovelace


def calc_pool_saturation(pool_stake: int, circulating_supply: int, n_opt: int) -> float:
    # !TODO: add docstring
    assert int(n_opt) > 0

    saturation_point = int(circulating_supply) / int(n_opt)
    return int(pool_stake) / saturation_point


def check_pool_is_valid(pool_id: str) -> bool:
    """Check if pool_id points to a valid pool or not."""

    try:
        BlockFrostAPI.api.pool(pool_id=pool_id)
        return True
    except ApiError:
        return False


def check_stake_addr_is_valid(stake_addr: str) -> bool:
    """Check if stake_addr points to a valid stake address or not."""

    try:
        BlockFrostAPI.api.account_addresses(stake_addr)
        return True
    except ApiError:
        return False
