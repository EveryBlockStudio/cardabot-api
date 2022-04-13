from datetime import datetime, timedelta

from dataclasses import dataclass
from urllib import response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
import requests

from .models import Chat
from .serializers import ChatSerializer
from .graphql_client import GRAPHQL
from . import utils


@dataclass
class QueryParameters:
    """Set of possible query parameters."""

    client_filter = "client_filter"
    currency_format = "currency_format"


@dataclass
class Const:
    """Set of constant variables."""

    SLOTS_EPOCH = 432000  # total slots in one epoch
    EPOCH_DURATION = 5  # days


class ChatList(APIView):
    """List all chats in the database or create a new one."""

    def get(self, request, format=None):
        chats = Chat.objects.all()
        if request.query_params.get(QueryParameters.client_filter) is not None:
            chats = chats.filter(
                client=request.query_params.get(QueryParameters.client_filter)
            )

        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatDetail(APIView):
    """Retrieve, update or delete a chat instance."""

    def get(self, request, chat_id: str, format=None):
        chat = self._get_object_by_chat_id(
            chat_id, request.query_params.get(QueryParameters.client_filter)
        )
        serializer = ChatSerializer(chat)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, chat_id: str, format=None):
        chat = self._get_object_by_chat_id(
            chat_id, request.query_params.get(QueryParameters.client_filter)
        )
        chat.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, chat_id: str, format=None):
        chat = self._get_object_by_chat_id(
            chat_id, request.query_params.get(QueryParameters.client_filter)
        )
        serializer = ChatSerializer(chat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_object_by_chat_id(self, chat_id: str, client: str = None):
        """Return chat object by chat_id and client (if provided)."""
        chats = Chat.objects.all()
        if client is not None:
            chats = chats.filter(client=client)

        try:
            return chats.get(chat_id=chat_id)
            # !TODO: how to deal with MultipleObjectsReturned?
        except Chat.DoesNotExist:
            raise Http404


class Epoch(APIView):
    """Get information about the Cardano current epoch."""

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
            "delegators_count": int(stakePoolDetails["stakePools"][0]["delegators_aggregate"]["aggregate"]["count"]),
            "epoch_blocks_count": int(stakePoolDetails["blocksThisEpoch"][0]["blocks_aggregate"]["aggregate"]["count"]),
            "lifetime_blocks_count": int(stakePoolDetails["lifetimeBlocks"][0]["blocks_aggregate"]["aggregate"]["count"]),
        }
        # fmt: on

        return Response({"data": response}, status=status.HTTP_200_OK)


class NetParams(APIView):
    """Get network parameters."""

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
