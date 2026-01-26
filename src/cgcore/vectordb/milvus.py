from typing import Optional, Union, List, Dict, Any
import os
import asyncio
from urllib.parse import urlparse
from pymilvus import AsyncMilvusClient, DataType
from cgcore.vectordb.base import BaseVectorDB
from cgcore.configs.vectordb.milvus import MilvusConfig

class MilvusDB(BaseVectorDB):
    def __init__(self, config: MilvusConfig):
        super().__init__(config)
        
        # 1. Setup Configs
        self.uri = os.getenv("MILVUS_URL", "http://localhost:19530")
        self.token = os.getenv("MILVUS_TOKEN", "")
        self.collection_name = self.config.collection_name
        
        # 2. Initialize Client
        self.client = AsyncMilvusClient(
            uri=self.uri,
            token=self.token,
        )
        print("AsyncMilvusClient initialized.")

        # 3. [CHANGED] Do NOT start the task yet. Just set it to None.
        # This prevents the DB from connecting until you actually ask for data.
        self._init_task = None

    async def _create_collection(self):
        """
        Native async collection setup.
        """
        try:
            if await self.client.has_collection(self.collection_name):
                print(f"Collection '{self.collection_name}' already exists. Skipping creation.")
                return

            schema = self.client.create_schema(
                auto_id=True,
                enable_dynamic_field=True,
            )
            
            schema.add_field(field_name="_id", datatype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=128)
            schema.add_field(field_name="doc_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=int(self.config.dimensions))
            schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="meta_data", datatype=DataType.JSON, nullable=True)
            
            index_params = self.client.prepare_index_params()
            index_params.add_index(field_name="_id", index_type="AUTOINDEX")
            index_params.add_index(
                field_name="vector",
                index_type="HNSW",
                index_name="vector_index",
                metric_type="L2",
                params={"M": 64, "efConstruction": 100}
            )
            
            await self.client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params
            )
            print(f"Collection '{self.collection_name}' created successfully.")

        except Exception as e:
            print(f"Milvus setup background task failed: {e}")
            raise e

    async def _ensure_ready(self):
        """
        [CHANGED] If the task hasn't started yet, start it NOW.
        Then wait for it to finish.
        """
        if self._init_task is None:
            # First time usage: Fire the background task
            self._init_task = asyncio.create_task(self._create_collection())
        
        # Wait for the task (whether we just started it or it was running)
        await self._init_task

    async def insert(self, records: List[Dict[str, Any]]):
        await self._ensure_ready() # Triggers connection if not connected
        try:
            await self.client.insert(
                collection_name=self.collection_name,
                data=records
            )
            return True
        except Exception as e:
            print(f"[Milvus] Insert error: {e}")
            return False

    async def get(self, _id, **kwargs):
        await self._ensure_ready()
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["vector", "content", "_id", "meta_data"]

        return await self.client.query(
            collection_name=self.collection_name,
            filter=f"_id == '{_id}'", 
            output_fields=kwargs.get("output_fields")
        )

    async def query(self, **kwargs): 
        await self._ensure_ready()
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["vector", "content", "_id", "meta_data"]
            
        if not kwargs.get("filter"):
            raise ValueError("Filter must be provided")

        return await self.client.query(
            collection_name=self.collection_name,
            filter=kwargs["filter"],
            output_fields=kwargs["output_fields"],
        )

    async def vector_search(self, vector, top_k=5, **kwargs):
        await self._ensure_ready()
        
        if len(vector) != int(self.config.dimensions):
            raise ValueError(f"Query embedding dimension mismatch.")
        
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["doc_id", "vector", "content", "_id", "meta_data"]

        search_params = kwargs.get("search_params", {"metric_type": "L2", "params": {"nprobe": 10}})

        res = await self.client.search(
            collection_name=self.collection_name,
            data=[vector],
            limit=top_k,
            output_fields=kwargs["output_fields"],
            anns_field="vector",
            search_params=search_params,
            filter=kwargs.get("filter", "") 
        )

        formatted_results = []
        if res and len(res) > 0:
            for hit in res[0]:
                doc = {
                    "content": hit.get("entity", {}).get("content") or hit.get("content", ""),
                    "_id": hit.get("id") or hit.get("_id", ""),
                    "meta_data": hit.get("entity", {}).get("meta_data") or hit.get("meta_data", {}),
                    "distance": hit.get("distance", 0.0)
                }
                formatted_results.append(doc)
        
        return formatted_results

    async def delete(self, _ids: list[str]):
        await self._ensure_ready()
        if not _ids: raise ValueError("IDs cannot be empty")
        
        filter_expr = f"_id in {str(_ids)}"
        await self.client.delete(
            collection_name=self.collection_name,
            filter=filter_expr
        )
    
    async def delete_collection(self):
        """
        Completely deletes the entire collection.
        """
        await self._ensure_ready()

        try:
            await self.client.drop_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' completely deleted")
            return True
        except Exception as e:
            print(f"Error deleting collection '{self.collection_name}': {e}")
            return False
            
    async def close(self):
        await self.client.close()