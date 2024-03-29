from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import utils
from .graphql_client import GRAPHQL
from .views import QueryParameters


@dataclass
class Const:
    """Set of constant variables."""

    SLOTS_EPOCH = 432000  # total slots in one epoch
    EPOCH_DURATION = 5  # days


class Epoch(APIView):
    """Get information about the Cardano current epoch."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        # gql queries
        currentEpochTip = GRAPHQL("currentEpochTip.graphql").get("data")
        epochInfo = GRAPHQL(
            "epochInfo.graphql",
            {"epoch": currentEpochTip["cardano"]["currentEpoch"]["number"]},
        ).get("data")

        started_at = datetime.fromisoformat(
            epochInfo["epochs"][0]["startedAt"][:-1]  # remove trailing "Z" timestamp
        )

        remaining_time = (
            started_at + timedelta(days=Const.EPOCH_DURATION) - datetime.utcnow()
        ).total_seconds()

        percentage = (
            currentEpochTip["cardano"]["tip"]["slotInEpoch"] / Const.SLOTS_EPOCH
        )

        # fmt: off
        # convert lovelace values to ada if needed
        fees_in_epoch, active_stake = utils.values_to_ada(
            [
                epochInfo["epochs"][0]["fees"],
                epochInfo["epochs"][0]["activeStake_aggregate"]["aggregate"]["sum"]["amount"],
            ],
            request.query_params.get(QueryParameters.currency_format),
        )

        response = {
            "percentage": percentage * 100,
            "current_epoch": currentEpochTip["cardano"]["currentEpoch"]["number"],
            "current_slot": currentEpochTip["cardano"]["tip"]["slotNo"],
            "slot_in_epoch": currentEpochTip["cardano"]["tip"]["slotInEpoch"],
            "txs_in_epoch": int(epochInfo["epochs"][0]["transactionsCount"]),
            "fees_in_epoch": fees_in_epoch,
            "active_stake": active_stake,
            "n_active_stake_pools": int(epochInfo["stakePools_aggregate"]["aggregate"]["count"]),
            "remaining_time": remaining_time,
        }
        # fmt: on

        return Response({"data": response}, status=status.HTTP_200_OK)


class StakePool(APIView):
    """Get infos from a stake pool."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

    def get(self, request, pool_id: str, format=None):
        """Retrieve info from a stake pool.

        Args:
            pool_id (path param): stake pool id (BECH32).
            currency_format (query param): currency format (ADA or LOVELACE).

        Returns:
            A dict with the query result.

        """
        epoch = GRAPHQL.this_epoch

        adaSupply = GRAPHQL("adaSupply.graphql").get("data")
        activeStake = GRAPHQL(
            "epochActiveStakeNOpt.graphql",
            variables={"epoch": epoch},
        ).get("data")

        stakePoolDetails = GRAPHQL(
            "stakePoolDetails.graphql",
            variables={"pool": pool_id, "epoch": epoch},
        ).get("data")

        try:
            url = stakePoolDetails["stakePools"][0]["url"]
        except (IndexError, TypeError):  # pool not found
            raise Http404

        res = requests.get(url)  # get pool metadata
        metadata = res.json() if res.json() else {}

        # fmt: off
        stake = stakePoolDetails["stakePools"][0]["activeStake_aggregate"]["aggregate"]["sum"]["amount"]
        total_stake = activeStake["epochs"][0]["activeStake_aggregate"]["aggregate"]["sum"]["amount"]
        circulating_supply = adaSupply["ada"]["supply"]["circulating"]
        n_opt = activeStake["epochs"][0]["protocolParams"]["nOpt"]

        controlled_stake_percentage = (int(stake) / int(total_stake)) * 100
        saturation = utils.calc_pool_saturation(stake, circulating_supply, n_opt)

        # convert values to ada if needed
        fixed_cost, pledge, stake = utils.values_to_ada(
            [
                stakePoolDetails["stakePools"][0]["fixedCost"], 
                stakePoolDetails["stakePools"][0]["pledge"],
                stake,
            ],
            request.query_params.get(QueryParameters.currency_format),
        )

        response = {
            "ticker": metadata.get("ticker", "NOT FOUND."),
            "name": metadata.get("name", "NOT FOUND."),
            "description": metadata.get("description", "NOT FOUND."),
            "homepage": metadata.get("homepage", "NOT FOUND."),
            "pool_id": stakePoolDetails["stakePools"][0]["id"],
            "pledge": pledge,
            "fixed_cost": fixed_cost,
            "margin": stakePoolDetails["stakePools"][0]["margin"] * 100,
            "saturation": saturation * 100,  # !TODO: fix
            "controlled_stake_percentage": controlled_stake_percentage,  # !TODO: fix
            "active_stake_amount": stake,  # !TODO: fix
            "delegators_count": int(stakePoolDetails["stakePools"][0]["activeStake_aggregate"]["aggregate"]["count"]),
            "epoch_blocks_count": int(stakePoolDetails["blocksThisEpoch"][0]["blocks_aggregate"]["aggregate"]["count"]),
            "lifetime_blocks_count": int(stakePoolDetails["lifetimeBlocks"][0]["blocks_aggregate"]["aggregate"]["count"]),
        }
        # fmt: on

        return Response({"data": response}, status=status.HTTP_200_OK)


class NetParams(APIView):
    """Get network parameters."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

    def get(self, request, format=None):
        epoch = GRAPHQL.this_epoch
        netParams = GRAPHQL("netParams.graphql", {"epoch": epoch}).get("data")[
            "epochs"
        ][0]

        min_pool_cost, min_utxo_value = utils.values_to_ada(
            [
                int(netParams["protocolParams"]["minPoolCost"]),
                int(netParams["protocolParams"]["minUTxOValue"]),
            ],
            request.query_params.get(QueryParameters.currency_format),
        )

        response = {
            "a0": netParams["protocolParams"]["a0"],
            "min_pool_cost": min_pool_cost,
            "min_utxo_value": min_utxo_value,
            "n_opt": netParams["protocolParams"]["nOpt"],
            "rho": netParams["protocolParams"]["rho"],
            "tau": netParams["protocolParams"]["tau"],
        }

        return Response({"data": response}, status=status.HTTP_200_OK)


class Pots(APIView):
    """Get pot infos."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

    def get(self, request, format=None):
        epoch = GRAPHQL.this_epoch
        adaPot = GRAPHQL("adaPot.graphql", {"epoch": epoch}).get("data")["epochs"][0]

        treasury, reserves, fees, rewards, utxo, deposits = utils.values_to_ada(
            [
                int(adaPot["adaPots"]["treasury"]),
                int(adaPot["adaPots"]["reserves"]),
                int(adaPot["adaPots"]["fees"]),
                int(adaPot["adaPots"]["rewards"]),
                int(adaPot["adaPots"]["utxo"]),
                int(adaPot["adaPots"]["deposits"]),
            ],
            request.query_params.get(QueryParameters.currency_format),
        )

        response = {
            "treasury": treasury,
            "reserves": reserves,
            "fees": fees,
            "rewards": rewards,
            "utxo": utxo,
            "deposits": deposits,
        }

        return Response({"data": response}, status=status.HTTP_200_OK)


class Netstats(APIView):
    """Get network stats."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

    def get(self, request, format=None):
        now = datetime.utcnow()
        params = {
            "epoch": GRAPHQL.this_epoch,
            "time_15m": (now - timedelta(hours=0.25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "time_1h": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "time_24h": (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        netstats = GRAPHQL("netstats.graphql", params).get("data")

        s = netstats["epochs"][0]["activeStake_aggregate"]["aggregate"]["sum"]["amount"]
        stake_percentage = int(s) / int(netstats["ada"]["supply"]["circulating"]) * 100

        max_block_size = netstats["epochs"][0]["protocolParams"]["maxBlockBodySize"]
        block_size_avg_15m = netstats["blocks_avg_15m"]["aggregate"]["avg"]["size"]
        block_size_avg_1h = netstats["blocks_avg_1h"]["aggregate"]["avg"]["size"]
        block_size_avg_24h = netstats["blocks_avg_24h"]["aggregate"]["avg"]["size"]

        response = {
            "ada_in_circulation": utils.values_to_ada(
                [int(netstats["ada"]["supply"]["circulating"])],
                request.query_params.get(QueryParameters.currency_format),
            )[0],
            "percentage_in_stake": stake_percentage,
            "stakepools": int(netstats["stakePools_aggregate"]["aggregate"]["count"]),
            "delegations": int(
                netstats["epochs"][0]["activeStake_aggregate"]["aggregate"]["count"]
            ),
            "load_15m": block_size_avg_15m / max_block_size * 100,
            "load_1h": block_size_avg_1h / max_block_size * 100,
            "load_24h": block_size_avg_24h / max_block_size * 100,
        }

        return Response({"data": response}, status=status.HTTP_200_OK)

class EpochSummary(APIView):
    """Get epoch summary."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

    def get(self, request, format=None):
        epoch = GRAPHQL.this_epoch - 1
        epoch_summary = GRAPHQL("epochDetailsByNumber.graphql", {"number": epoch}).get("data")["epochs"][0]

        fees, rewards, reserves, treasury = utils.values_to_ada(
            [
                int(epoch_summary["fees"]),
                int(epoch_summary["adaPots"]["rewards"]),
                int(epoch_summary["adaPots"]["reserves"]),
                int(epoch_summary["adaPots"]["treasury"]),
            ],
            request.query_params.get(QueryParameters.currency_format),
        )

        response = {
            "epoch": epoch,
            "blocks": epoch_summary["blocksCount"],
            "txs": epoch_summary["transactionsCount"],
            "fees": fees,
            "rewards": rewards,
            "reserves": reserves,
            "treasury": treasury,
        }

        return Response({"data": response}, status=status.HTTP_200_OK)
