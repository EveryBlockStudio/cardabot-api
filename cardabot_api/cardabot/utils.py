"""Helper functions for the cardabot endpoints."""


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
