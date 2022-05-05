from dataclasses import dataclass
import os
import logging
from operator import itemgetter

from pycardano import (
    Address,
    BlockFrostChainContext,
    Network,
    Transaction,
    TransactionBuilder,
    TransactionOutput,
    TransactionWitnessSet,
)

# import dotenv
# dotenv.load_dotenv()


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
    print(amounts)
    return sum(
        [
            int(amount.quantity)
            for amount in amounts
            if amount.unit.lower() == "lovelace"
        ]
    )


def select_pay_addr(
    pay_addresses: list[str], recipients: list[tuple[str, float]]
) -> list[str]:
    """This function is used to select a number of pay addresses for the tx.

    Sort pay addresses by balance and return just the ones needed to complete the tx.

    Args:
        pay_addresses: list of senders address in bech32 format.
        recipients: list of recipients' addresses in bech32 format and amounts.

    Returns:
        A list of pay addresses necessary to complete the tx, in bech32 format.

    Raises:
        ApiError: if the verification is not successful.
    """

    pay_addrs_balance = sorted(
        [(addr, _addr_balance(addr)) for addr in pay_addresses],
        key=itemgetter(1),
        reverse=True,
    )

    total_amount = sum([_to_llace(amount) for _, amount in recipients])
    sel_addrs, bal_sum = list(), 0

    for addr, balance in pay_addrs_balance:
        bal_sum += balance
        sel_addrs.append(addr)
        if bal_sum >= total_amount:
            break

    return sel_addrs


def build_unsigned_transaction(
    sender_stake_address: str, recipients: list[tuple[str, float]]
) -> str:
    """This function is used to build an unsigned transaction.

    Args:
        sender_stake_address: stake address in bech32 format.
        recipients: list of recipients' addresses in bech32 format and amounts.

    Returns:
        The usigned transaction in cbor format.

    Raises:
        ApiError: if the transaction is not built successfully.

    """
    senders = [
        item.address
        for item in ChainContext.api.account_addresses(sender_stake_address)
    ]

    input_addresses = [Address.decode(sender) for sender in senders]
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

    return Transaction(tx_body, TransactionWitnessSet()).to_cbor()


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
