from itertools import accumulate
import logging
import os
from dataclasses import dataclass
from operator import itemgetter
import re

from pycardano import (
    Address,
    BlockFrostChainContext,
    Network,
    Transaction,
    TransactionBuilder,
    TransactionOutput,
    TransactionWitnessSet,
)


@dataclass
class ChainContext:
    """This class is used to store the context of the chain."""

    network = Network.TESTNET if os.environ["NETWORK"] == "testnet" else Network.MAINNET
    context = BlockFrostChainContext(os.environ.get("BLOCKFROST_ID"), network=network)
    api = (
        context.api
    )  # blockfrost api obj, see: https://github.com/blockfrost/blockfrost-python


def _to_llace(amount: float) -> int:
    """This function is used to convert an amount in ADA to lovelace."""
    return int(round(amount, 6) * 1000000)


def _addr_balance(address: str) -> int:
    """Get the total balance (lovelace) of an address."""

    amounts = ChainContext.api.address(address).amount
    return sum(
        [
            int(amount.quantity)
            for amount in amounts
            if amount.unit.lower() == "lovelace"
        ]
    )


def get_pay_addr_from_stake_addr(stake_addr: str) -> str or None:
    """Return the first pay address from a staking address."""
    addresses = ChainContext.api.account_addresses(stake_addr)
    return addresses[0].address if addresses else None


def select_pay_addr(stake_addr: str, recipients: list[tuple[str, float]]) -> list[str]:
    """Select pay addresses for the tx.

    Sort pay addresses by balance and return just the ones needed to complete the tx.

    Args:
        stake_addr: the staking address of the sender in bech32 format.
        recipients: list of recipients' addresses in bech32 format and amounts.

    Returns:
        A list of pay addresses necessary to complete the tx, in bech32 format.
        If there aren't enough funds, returns empty list.
    """

    pay_addresses = [
        item.address for item in ChainContext.api.account_addresses(stake_addr, gather_pages=True, order="desc")
    ]

    total_amount = sum([_to_llace(amount) for _, amount in recipients])
    fee = _to_llace(float(os.environ["FEE_UBOUND"]))

    selected_addresses = []
    accumulate_amount = 0
    for pay_address in pay_addresses:
        addr_balance = _addr_balance(pay_address)

        # if the balance is greater than the total amount + fee, we can use this address
        if addr_balance >= total_amount + fee:
            return [pay_address]
        
        # otherwise, we accumulate the balance and keep looking for more addresses
        elif addr_balance > 0:
            selected_addresses.append(pay_address)
            accumulate_amount += addr_balance
        
            # check if accumulated amount is enough to complete the tx
            if accumulate_amount >= total_amount + fee:
                return selected_addresses

    # if we reach this point, there aren't enough funds
    return []


def build_unsigned_transaction(
    sender_addresses: list[str], recipients: list[tuple[str, float]]
) -> str:
    """Build an unsigned transaction.

    The balance of each sender address must add up to the total amount of the tx + fee.

    Args:
        sender_addresses: list of sender addresses in bech32 format.
        recipients: list of recipients' addresses in bech32 format and amounts.

    Returns:
        The unsigned transaction in cbor format.

    """
    input_addresses = [Address.decode(sender) for sender in sender_addresses]
    change_address = input_addresses[0]  # return change to the first sender address

    output_addresses = [
        TransactionOutput(Address.decode(recipient), _to_llace(amount))
        for recipient, amount in recipients
    ]

    builder = TransactionBuilder(ChainContext.context)

    for input_address in input_addresses:
        builder.add_input_address(input_address)
    for transaction_output in output_addresses:
        builder.add_output(transaction_output)

    tx_body = builder.build(change_address=change_address)

    logging.debug(
        repr(
            {
                "message": "Unsigned tx successfully built.",
                "data": {
                    "inputs:": input_addresses,
                    "outputs:": output_addresses,
                    "change:": change_address,
                },
            }
        )
    )

    return Transaction(tx_body, TransactionWitnessSet())


def compose_signed_transaction(unsigned_tx: str, witness: str) -> str:
    """This function is used to compose a signed transaction.

    Args:
        unsigned_tx: unsigned transaction in cbor format.
        witness: witness returned after signing tx, in cbor format.

    Returns:
        The signed transaction in cbor format, ready for submission.

    """
    tx = Transaction.from_cbor(unsigned_tx)
    witness = TransactionWitnessSet.from_cbor(witness)
    tx.transaction_witness_set = witness

    logging.debug(
        repr({"message": "Signed tx successfully composed.", "data": {"tx_id": tx.id}})
    )

    return tx.to_cbor()


if __name__ == "__main__":
    pass
