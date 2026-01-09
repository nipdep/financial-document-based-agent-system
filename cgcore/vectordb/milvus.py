from typing import Optional, Union, List, Dict, Any

import os
import numpy as np
from urllib.parse import urlparse
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility, MilvusClient
import asyncio
from cgcore.vectordb.base import BaseVectorDB
from cgcore.configs.vectordb.milvus import MilvusConfig

from icecream import ic
import uuid

class MilvusDB(BaseVectorDB):
    def __init__(self, config: MilvusConfig):
        super().__init__(config)
        self._create_client()
        

    def _create_client(self):
        self.client = MilvusClient(
            uri=os.getenv("MILVUS_URL", ""),
            token=os.getenv("MILVUS_TOKEN", ""),
        )
        
        # Parse host and port
        milvus_url = os.getenv("MILVUS_URL", "localhost:19530")
        u = urlparse(milvus_url if "://" in milvus_url else f"//{milvus_url}")
        self.host = u.hostname or milvus_url
        self.port = u.port or 19530
        
        print("MilvusClient connected.")
        
        self.db = self.client
        self.collection_name = self.config.collection_name

        self._create_collection()

    def _create_collection(self) -> Collection:
        """
        Checks if the collection exists. If not, creates it and adds a vector index.
        """
        
        try:
            connections.connect(alias="default", host=self.host, port=str(self.port))
            print(f"pymilvus ORM connected to {self.host}:{self.port} for setup.")
        except Exception as e:
            print(f"pymilvus ORM connection failed: {e}")
            # If connection fails, we can't proceed with setup
            raise e
        
        
        
        # Create question collection if it doesn't exist
        if not utility.has_collection(self.collection_name):
            schema = self.client.create_schema(
                auto_id=True,
                enable_dynamic_field=True,
            )
            
            # 3.2. Add fields to schema
            schema.add_field(
                field_name="_id", datatype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=128)
            schema.add_field(
                field_name="doc_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(
                field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=int(self.config.dimensions))
            schema.add_field(
                field_name="content", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(
                field_name="meta_data", datatype=DataType.JSON, nullable=True)
            
            index_params = self.client.prepare_index_params()

            # 3.4. Add indexes
            index_params.add_index(
                field_name="_id",
                index_type="AUTOINDEX"
            )

            index_params.add_index(
                field_name="vector",
                index_type="HNSW", # Type of the index to create
                index_name="vector_index", # Name of the index to create
                metric_type="L2", # Metric type used to measure similarity
                params={
                    "M": 64, # Maximum number of neighbors each node can connect to in the graph
                    "efConstruction": 100 # Number of candidate neighbors considered for connection during index construction
                } # Index building params
            )
            
            
            self.client.create_collection(
                self.collection_name,
                schema=schema,
                index_params=index_params
            )

            print(f"Collection '{self.collection_name}' created.")

        else:
            print(
                f"Collection '{self.collection_name}' already exists. Skipping creation."
            )

    async def insert(self, records: List[Dict[str, Any]]):
        """
        Inserts one or more documents with their embeddings.

        :param records: List of document records with fields: vector, content, doc_id, meta_data.
        :return: True if insertion successful, False otherwise.
        """

        try:
            await asyncio.to_thread(
                self.client.insert,
                collection_name=self.collection_name,
                data=records
            )
            return True
        except Exception as e:
            print(f"[Milvus] Insert error: {e}")
            return False

    async def get(self, _id, **kwargs):
        """
        Retrieves a document by its ID.

        :param _id: The document ID.
        :return: The document.
        """
        
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["vector", "text", "id"]

        return await asyncio.to_thread(
            self.client.query,
            collection_name=self.collection_name,
            ids=[_id],
            output_fields=kwargs.get("output_fields")
        )

    def query(self, **kwargs):  # XXX: to improve
        """
        Retrieves the top-k most similar documents based on text similarity.

        :param pipeline: The aggregation pipeline to use.
        :return: List of retrieved documents.
        """
        
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["vector", "text", "id"]
            
        if not kwargs.get("filter"):
            raise ValueError("Filter must be provided")

        res = self.client.query(
            collection_name=self.collection_name,
            filter=kwargs["filter"],
            output_fields=kwargs["output_fields"],
        )
        return res

    async def vector_search(self, vector, top_k=5, **kwargs):
        """
        Retrieves the top-k most similar documents based on vector similarity.
        Returns format compatible with chatgenie library.
        """
        if len(vector) != int(self.config.dimensions):
            raise ValueError(
                f"Query embedding must be of dimension {int(self.config.dimensions)}"
            )
        
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["doc_id","vector", "content", "_id", "meta_data"]
        def _execute_search():
            if not kwargs.get("filter"):
                return self.client.search(
                    collection_name=self.collection_name,
                    data=[vector],
                    limit=top_k,
                    output_fields=kwargs["output_fields"],
                    anns_field="vector",
                    search_params=kwargs.get("search_params", None),
                )
            else:
                return self.client.search(
                    collection_name=self.collection_name,
                    data=[vector],
                    limit=top_k,
                    output_fields=kwargs["output_fields"],
                    anns_field="vector",
                    search_params=kwargs.get("search_params", None),
                    filter=kwargs["filter"],
                )
        res = await asyncio.to_thread(_execute_search)
        # Convert MilvusDB result to chatgenie-compatible format
        formatted_results = []
        
        if res and len(res) > 0:
            # MilvusDB returns list of lists - first list contains results for first query
            search_results = res[0]
            
            for hit in search_results:
                # Extract fields - try multiple access patterns
                if hasattr(hit, 'entity'):
                    content = hit.entity.get("content", "")
                    _id = hit.entity.get("_id", "")
                    meta_data = hit.entity.get("meta_data", {})
                else:
                    # Try direct dictionary access
                    content = hit.get("content", "")
                    _id = hit.get("_id", "")
                    meta_data = hit.get("meta_data", {})
                
                # CRITICAL DEBUG: Print full content
                print(f"[DEBUG FULL CONTENT] ID: {_id}")
                print(f"[DEBUG FULL CONTENT] Content: '{content}'")  # Full content, not truncated
                print(f"[DEBUG FULL CONTENT] Content length: {len(content)}")
                print(f"[DEBUG FULL CONTENT] Metadata: {meta_data}")
                
                doc = {
                    "content": content,
                    "_id": _id,
                    "meta_data": meta_data,
                }
                
                if hasattr(hit, 'distance'):
                    doc["distance"] = hit.distance
                
                formatted_results.append(doc)
                
                # DEBUG: Print formatted result
                print(f"[DEBUG] Formatted chunk: content={doc['content'][:50]}..., distance={doc.get('distance')}")
        
        print(f"[DEBUG] Returning {len(formatted_results)} formatted results")
        return formatted_results

    async def delete(self, _ids: list[str]):
        """
        Deletes documents by their IDs.

        :param _ids: List of document IDs to delete.
        """
        if not _ids:
            raise ValueError("List of IDs to delete cannot be empty")

        await asyncio.to_thread(
            self.client.delete,
            collection_name=self.collection_name,
            ids=_ids,
        )
        
    
