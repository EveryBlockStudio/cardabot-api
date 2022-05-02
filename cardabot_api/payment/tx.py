from dataclasses import dataclass
import os
import logging

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
    bfrost_api = (
        context.api
    )  # blockfrost api obj, see: https://github.com/blockfrost/blockfrost-python


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
        for item in ChainContext.bfrost_api.account_addresses(sender_stake_address)
    ]

    input_addresses = [Address.decode(sender) for sender in senders]
    change_address = input_addresses[0]  # return change to the first sender address

    output_addresses = [
        TransactionOutput(Address.decode(recipient), int(round(amount, 6) * 1000000))
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
