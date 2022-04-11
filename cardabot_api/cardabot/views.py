from datetime import datetime, timedelta
import json

from dataclasses import dataclass
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404, JsonResponse

from .models import Chat
from .serializers import ChatSerializer
from .graphql_client import GRAPHQL
from . import utils


@dataclass
class QueryParameters:
    """Set of possible query parameters."""

    client_filter = "client_filter"


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

    def get(request, format=None):
        # gql queries
        currentEpochTip = GRAPHQL("currentEpochTip.graphql").get("data")
        epochInfo = GRAPHQL(
            "epochInfo.graphql",
            {"epoch": currentEpochTip["cardano"]["currentEpoch"]["number"]},
        ).get("data")

        started_at = datetime.fromisoformat(
            epochInfo["epochs"][0]["startedAt"][:-1]  # remove trailing "Z" of timestamp
        )

        remaining_time = (
            started_at + timedelta(days=Const.EPOCH_DURATION) - datetime.utcnow()
        ).total_seconds()

        percentage = (
            currentEpochTip["cardano"]["tip"]["slotInEpoch"] / Const.SLOTS_EPOCH
        )

        # fmt: off
        response = {
            "perc": percentage * 100,
            "current_epoch": currentEpochTip["cardano"]["currentEpoch"]["number"],
            "current_slot": currentEpochTip["cardano"]["tip"]["slotNo"],
            "slot_in_epoch": currentEpochTip["cardano"]["tip"]["slotInEpoch"],
            "txs_in_epoch": int(epochInfo["epochs"][0]["transactionsCount"]),
            "fees_in_epoch": utils.fmt_ada(epochInfo["epochs"][0]["fees"]),
            "active_stake": utils.fmt_ada(epochInfo["epochs"][0]["activeStake_aggregate"]["aggregate"]["sum"]["amount"]),
            "n_active_stake_pools": int(epochInfo["stakePools_aggregate"]["aggregate"]["count"]),
            "remaning_time": remaining_time,
        }
        # fmt: on

        return Response({"data": response}, status=status.HTTP_200_OK)
