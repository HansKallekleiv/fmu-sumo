from sumo.wrapper import SumoClient
from fmu.sumo.explorer.utils import Utils
from typing import List, Dict


class DocumentCollection:
    """Class for representing a collection of documents in Sumo"""

    def __init__(
        self,
        type: str,
        sumo: SumoClient,
        query: Dict = None,
    ):
        self._utils = Utils(sumo)
        self._type = type
        self._sumo = sumo
        self._after = None
        self._curr_index = 0
        self._len = None
        self._items = []
        self._field_values = {}
        self._query = self._init_query(type, query)

    def __len__(self) -> int:
        """Get size of document collection

        Returns:
            Document collection size
        """
        if self._len is None:
            self._len = self._utils.get_doc_count(self._query)

        return self._len

    def __getitem__(self, index: int) -> Dict:
        """Get document

        Arguments:
            - index (int): index

        Returns:
            A document at a given index
        """
        if index >= self.__len__():
            raise IndexError

        if len(self._items) <= index:
            while len(self._items) <= index:
                next_batch = self._next_batch()

                if len(next_batch) > 0:
                    self._items.extend(next_batch)
                else:
                    raise IndexError

        return self._items[index]

    def _get_field_values(self, field: str) -> List:
        """Get List of unique values for a given field in the document collection

        Arguments:
            - field (str): a metadata field

        Returns:
            A List of unique values for the given field
        """
        if field not in self._field_values:
            buckets = self._utils.get_buckets(field, self._query)
            self._field_values[field] = list(map(lambda bucket: bucket["key"], buckets))

        return self._field_values[field]

    def _next_batch(self) -> List[Dict]:
        """Get next batch of documents

        Returns:
            The next batch of documents
        """
        query = {
            "query": self._query,
            "sort": [{"_doc": {"order": "desc"}}],
            "size": 500,
        }

        if self._after is not None:
            query["search_after"] = self._after

        res = self._sumo.post("/search", json=query)
        hits = res.json()["hits"]["hits"]

        if len(hits) > 0:
            self._after = hits[-1]["sort"]

        return hits

    def _init_query(self, type: str, query: Dict = None) -> Dict:
        """Initialize base filter for document collection

        Arguments:
            - type (str): object type
            - filters (List[Dict]): a List of filters

        Returns:
            Document collection base filters
        """
        class_filter = {"bool": {"must": [{"term": {"class.keyword": type}}]}}

        if query is not None:
            return self._utils.extend_query_object(class_filter, query)
        
        return class_filter

    def _add_filter(self, query: Dict) -> Dict:
        """Add filter to DocumentCollection base filter

        Argmuments:
            - user_filter (Dict[str, List]): new filters

        Returns:
            Filter object containing base filters and new filters
        """

        return self._utils.extend_query_object(self._query, query)
