import secrets
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
from .models import CardaBotUser, Chat
from .serializers import (
    CardaBotUserSerializer,
    ChatSerializer,
    TemporaryTokenSerializer,
)


@dataclass
class QueryParameters:
    """Set of possible query parameters."""

    client_filter = "client_filter"
    currency_format = "currency_format"


@dataclass
class BodyParameters:
    """Set of possible body parameters."""

    cardabot_user = "cardabot_user"  # holds user's stake address
    tmp_token = "tmp_token"


@dataclass
class Const:
    """Set of constant variables."""

    SLOTS_EPOCH = 432000  # total slots in one epoch
    EPOCH_DURATION = 5  # days


class CardaBotUserList(APIView):
    """
    List all users, or create a new user.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """Return a list of all users."""
        users = CardaBotUser.objects.all()
        serializer = CardaBotUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """Create a new user."""
        serialized = self.serialize_and_create_new_user(request.data)
        return Response(serialized["res"], status=serialized["status"])

    @staticmethod
    def serialize_and_create_new_user(data):
        """Create a new user.

        Args:
            data (dict): The data to be serialized and saved.

        Returns:
           tuple: The serialized data and the status code.
        """
        serializer = CardaBotUserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return {"res": serializer.data, "status": status.HTTP_201_CREATED}
        return {"res": serializer.errors, "status": status.HTTP_400_BAD_REQUEST}


class CardaBotUserDetail(APIView):
    """Retrieve or delete a user."""

    permission_classes = (IsAuthenticated,)

    def get_object(self, pk: int):
        try:
            return CardaBotUser.objects.get(pk=pk)
        except CardaBotUser.DoesNotExist:
            raise Http404

    def get(self, request, pk: int, format=None):
        user = self.get_object(pk)
        serializer = CardaBotUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatList(APIView):
    """List all chats in the database or create a new one."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

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

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

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

        cardabot_user = request.data.get(BodyParameters.cardabot_user)
        if cardabot_user:
            try:
                chat = self.update_chat_cardabot_user(
                    chat=chat, stake_address=cardabot_user
                )
            except Http404:
                return Response(
                    {"error": "CardaBot user not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = ChatSerializer(chat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update_chat_cardabot_user(chat: Chat, stake_address: str):
        if not CardaBotUser.objects.filter(stake_key=stake_address).exists():
            raise Http404("CardaBotUser not found.")

        chat.cardabot_user = CardaBotUser.objects.get(stake_key=stake_address)
        chat.save()
        return chat

    @staticmethod
    def _get_object_by_chat_id(chat_id: str, client: str = None):
        """Return chat object by chat_id and client (if provided)."""
        chats = Chat.objects.all()
        if client is not None:
            chats = chats.filter(client=client)

        try:
            return chats.get(chat_id=chat_id)
            # !TODO: how to deal with MultipleObjectsReturned?
        except Chat.DoesNotExist:
            raise Http404


class TemporaryChatToken(APIView):
    """Generate temporary wallet connection token for a chat."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, chat_id: str, format=None):
        """Generate a temporary token for this chat_id."""
        chat = ChatDetail._get_object_by_chat_id(
            chat_id, request.query_params.get(QueryParameters.client_filter)
        )

        tmp_token = secrets.token_urlsafe(nbytes=32)
        serializer = TemporaryTokenSerializer(
            chat, data={"tmp_token": tmp_token}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateAndConnectUser(APIView):
    """Connect a CardaBotUser with a Chat using the temporay token.

    If the CardaBotUser already exists, there is no need to create a new one -- the chat
    will be connected to it.

    Delete the temporary token after the connection is established.

    Raises:
        Http404: if the temporary token is not found.
        Http400: if stake address is not valid (not a valid CardaBotUser).

    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        # get chat
        tmp_token = request.data.get(BodyParameters.tmp_token)
        try:
            chat = self._get_chat_by_tmp_token(tmp_token)
        except Http404:
            return Response(
                {"error": "Temporary token not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # create cardabot user
        stake_address = request.data.get(BodyParameters.cardabot_user)
        serialized_user = CardaBotUserList.serialize_and_create_new_user(
            {"stake_key": stake_address}
        )

        if serialized_user["status"] != status.HTTP_201_CREATED:
            # if stake_key already exists, do nothing. otherwise, return error
            # if stake_key already exists, this expects the following error:
            # "{
            #     "stake_key": [
            #         "carda bot user with this stake key already exists."
            #     ]
            # }
            # "
            if not serialized_user["res"].get("stake_key"):
                return Response(serialized_user["res"], serialized_user["status"])

        # connect chat and user
        try:
            ChatDetail.update_chat_cardabot_user(chat, stake_address)
        except Http404:
            return Response(
                {"error": "CardaBot user not found"}, status=status.HTTP_404_NOT_FOUND
            )

        chat.tmp_token = None  # reset token
        chat.save()

        return Response(
            {
                "success": f"CardaBotUser `{stake_address}` connected to chat `{chat.chat_id}`"
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_chat_by_tmp_token(self, tmp_token: str):
        """Return chat object by tmp_token."""
        if not tmp_token:
            raise Http404

        try:
            return Chat.objects.get(tmp_token=tmp_token)
        except Chat.DoesNotExist:
            raise Http404


class Epoch(APIView):
    """Get information about the Cardano current epoch."""

    permission_classes = (
        IsAuthenticated,
    )  # only authenticated users can access this view

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
