"""Helper functions for the cardabot endpoints."""


def lovelace_to_ada(lovelace_value: float) -> float:
    """Take a value in lovelace and return it in ADA."""
    constant = 1e6
    return int(lovelace_value) / constant


def calc_pool_saturation(pool_stake: int, circulating_supply: int, n_opt: int) -> float:
    # !TODO: add docstring
    assert n_opt > 0

    saturation_point = circulating_supply / n_opt
    return pool_stake / saturation_point
