from typing import Optional, Union, List

import os
import numpy as np
from pymilvus import DataType, MilvusClient, MilvusException

from chatgenie.vectordb.base import BaseVectorDB

from icecream import ic
import uuid

class MilvusDB(BaseVectorDB):
    def __init__(self, config):
        super().__init__(config)
        self._create_client()

    def _create_client(self):
        self.client = MilvusClient(
            uri=os.getenv("MILVUS_URL", ""),
            token=os.getenv("MILVUS_TOKEN", ""),
        )
        
        self.db = self.client

        self.collection_name = self.config.collection_name

        self._create_collection()

    def _create_collection(self):
        """
        Checks if the collection exists. If not, creates it and adds a vector index.
        """
        # Check if collection exists
        if not self.client.has_collection(self.collection_name):
            schema = self.client.create_schema(
                auto_id=False,
                enable_dynamic_field=True,
            )
            
            # 3.2. Add fields to schema
            schema.add_field(field_name="_id", datatype=DataType.VARCHAR, is_primary=True, max_length=128)
            schema.add_field(
                field_name="text_embedding", datatype=DataType.FLOAT_VECTOR, dim=int(self.config.dimensions)
            )
            schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(
                field_name="meta_data", datatype=DataType.JSON, nullable=True
            )
            
            index_params = self.client.prepare_index_params()

            # 3.4. Add indexes
            index_params.add_index(
                field_name="_id",
                index_type="AUTOINDEX"
            )

            index_params.add_index(
                field_name="text_embedding",
                index_type="AUTOINDEX",
                metric_type="COSINE"
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

    def insert(self, text, embedding):
        """
        Inserts a single document with its embedding.

        :param text: The original text.
        :param embedding: A list representing the embedding vector.
        """
        if len(embedding) != self.config.dimensions:
            raise ValueError(f"Embedding must be of dimension {self.config.dimensions}")

        # Generate a unique ID for the document
        doc_id = str(uuid.uuid4())

        doc = {"_id": doc_id, "content": text, "text_embedding": embedding}
        self.client.insert(
            collection_name=self.collection_name,
            data=[doc],
        )

    def batch_insert(self, documents):
        """
        Inserts multiple documents with embeddings.

        :param documents: A list of dictionaries with 'text' and 'vector' keys.
        """
        # ic(len(documents[0]["text_embedding"]))
        # ic(self.config.dimensions)
        for doc in documents:
            if len(doc["text_embedding"]) != int(self.config.dimensions):
                ic(len(doc["text_embedding"]), int(self.config.dimensions))
                raise ValueError(
                    f"Embedding must be of dimension {self.config.dimensions}"
                )

        self.client.insert(
            collection_name=self.collection_name,
            data=documents,
        )

    def get(self, _id, **kwargs):
        """
        Retrieves a document by its ID.

        :param _id: The document ID.
        :return: The document.
        """
        
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["vector", "text", "id"]
            
        return self.client.query(
            collection_name=self.collection_name,
            ids=[_id],
            output_fields=kwargs["output_fields"],
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

    def vector_search(self, vector, top_k=5, **kwargs):
        """
        Retrieves the top-k most similar documents based on vector similarity.
        Returns format compatible with chatgenie library.
        """
            
        if len(vector) != int(self.config.dimensions):
            raise ValueError(
                f"Query embedding must be of dimension {int(self.config.dimensions)}"
            )
        
        if not kwargs.get("output_fields"):
            kwargs["output_fields"] = ["text_embedding", "content", "_id", "meta_data"]

        if not kwargs.get("filter"):
            res = self.client.search(
                collection_name=self.collection_name,
                data=[vector],
                limit=top_k,
                output_fields=kwargs["output_fields"],
                anns_field="text_embedding",
                search_params=kwargs.get("search_params", None),
            )
        else:
            res = self.client.search(
                collection_name=self.collection_name,
                data=[vector],
                limit=top_k,
                output_fields=kwargs["output_fields"],
                anns_field="text_embedding",
                search_params=kwargs.get("search_params", None),
                filter=kwargs["filter"],
            )
        
        # print(f"[DEBUG] MilvusDB raw search result: {res}")
    
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

    def delete(self, _ids: list[str]):
        """
        Deletes documents by their IDs.

        :param _ids: List of document IDs to delete.
        """
        if not _ids:
            raise ValueError("List of IDs to delete cannot be empty")

        self.client.delete(
            collection_name=self.collection_name,
            ids=_ids,
        )
        
    
