from typing import Optional

from cgcore.configs.vectordb.base import BaseVectorDbConfig

class MilvusConfig(BaseVectorDbConfig):
    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        collection_name: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        """
        Initializes a configuration class instance for MilvusDB.

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
        super().__init__(
            url=url,
            token=token,
            collection_name=collection_name,
            dimensions=dimensions,
        )