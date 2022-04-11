"""Helper functions for the cardabot endpoints."""
from collections import OrderedDict


def lovelace_to_ada(lovelace_value: float) -> float:
    """Take a value in lovelace and return it in ADA."""
    constant = 1e6
    return lovelace_value / constant


def fmt_ada(lovelace_value: float) -> str:
    """Take lovelace convert to ADA and return string with formatted value."""
    units = OrderedDict({"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3})
    ada_value = lovelace_to_ada(int(lovelace_value))

    for key in units.keys():
        if ada_value > units.get(key):
            ada_fmt, best_unit = ada_value / units.get(key), key
            return f"{float(ada_fmt):.2f}{best_unit}"

    return f"{float(ada_value):.0f}"
