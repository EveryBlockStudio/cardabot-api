from dataclasses import dataclass
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404

from .models import Chat
from .serializers import ChatSerializer


@dataclass
class QueryParameters:
    """Set of possible query parameters."""

    client_filter = "client_filter"


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
