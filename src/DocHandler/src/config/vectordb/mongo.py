from typing import Optional

from chatgenie.config.vectordb.base import BaseVectorDbConfig
from chatgenie.helper.json_serializable import register_deserializable


@register_deserializable
class MongoConfig(BaseVectorDbConfig):
    def __init__(
        self,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        app_name: Optional[str] = None, # XXX: app_name is not used
        dbname: Optional[str] = None,
        collection_name: Optional[str] = None,
        dimensions: Optional[int] = None,
        top_k: Optional[int] = None,
        allow_reset=False,
        settings: Optional[dict] = None,
    ):
        """
        Initializes a configuration class instance for ChromaDB.

        :param username: username of the db server
        :type username: Optional[str], 
        :param password: password to the db server
        :type password: Optional[str]
        :param app_name: Cluster app_name of the db server
        :type app_name: Optional[str]
        :param dbname: db name in the cluster
        :type dbname: Optional[str]
        :param collection_name: Default name for the collection, defaults to None
        :type collection_name: Optional[str], optional
        :param dimensions: number of dimension in the vector db
        :type dir: Optional[str], optional
        :param allow_reset: Resets the database. defaults to False
        :type allow_reset: bool
        :param chroma_settings: Chroma settings dict, defaults to None
        :type chroma_settings: Optional[dict], optional
        """

        self.settings = settings
        self.allow_reset = allow_reset
        self.top_k = top_k
        super().__init__(api_key=api_key, collection_name=collection_name, username=username, password=password, app_name=app_name, dbname=dbname, dimensions=int(dimensions))
