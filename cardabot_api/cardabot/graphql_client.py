import os
import logging
from types import NoneType
from typing import Any
from sgqlc.endpoint.http import HTTPEndpoint


class GraphQLClient:
    def __init__(self, url: str, token: str = "") -> None:
        self.url = url
        self.token = token
        self.endpoint = HTTPEndpoint(url)

    def _caller(
        self,
        query_file: str,
        variables: dict = {},
        graphql_queries: str = "graphql_queries",
    ) -> dict:
        """Request data from a cardano graphql endpoint (EBS).

        Query text is obtained from `query_file` stored under the `graphql_queries` dir.
        """
        with open(os.path.join(graphql_queries, query_file)) as f:
            query = f.read()

        return self.endpoint(query, variables)

    @property
    def this_epoch(self) -> int:
        """Get the Cardano current epoch number."""
        currentEpochTip = self._caller("currentEpochTip.graphql").get("data")
        return int(currentEpochTip["cardano"]["currentEpoch"]["number"])

    def __call__(self, *args: Any, **kwds: Any) -> dict:
        """Request data from a cardano graphql endpoint (EBS).

        Args:
            query_file (str): name of the query file to be used.
            variables (dict): variables to be used in the query.
            graphql_queries (str): name of the dir where the query files are stored.
                Default is `graphql_queries/`.

        Returns:
            A dict with the processed response from the endpoint.
        """
        return self._caller(*args, **kwds)


GRAPHQL = GraphQLClient(url=os.environ.get("GRAPHQL_URL"))
