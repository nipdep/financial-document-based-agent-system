from typing import Optional 

from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

from chatgenie.vectordb.base import BaseVectorDB
from chatgenie.config.vectordb.mongo import MongoConfig

from icecream import ic

class MongoDB(BaseVectorDB):

    def __init__(self, config):
        super().__init__(config)
        self._create_client()

    def _create_client(self):
        URI = f"mongodb+srv://{self.config.username}:{self.config.password}@cluster0.ipcuk5d.mongodb.net/"
        self.client = MongoClient(URI)
        self.db = self.client[self.config.dbname]

        self.collection_name = self.config.collection_name
        
        self._create_collection()
        

    def _create_collection(self):
        """
        Checks if the collection exists. If not, creates it and adds a vector index.
        """
        # Check if collection exists
        if self.collection_name not in self.db.list_collection_names():
            self.db.create_collection(self.collection_name)
            self.collection = self.db[self.collection_name]

            ic(self.config.dimensions)
            # Define the vector search index
            search_index_model = SearchIndexModel(
                definition={
                    "fields": [
                    {
                        "type": "vector",
                        "path": "text_embedding",
                        "numDimensions": int(self.config.dimensions),
                        "similarity": "cosine",
                        "quantization": "scalar"
                    }
                    ]
                },
                name="vector_index",
                type="vectorSearch",
            )

            # Ensure the vector index is applied
            self.collection.create_search_index(search_index_model)
            print(f"✅ Collection '{self.collection_name}' created.")
        else:
            self.collection = self.db[self.collection_name]
            print(f"⚠️ Collection '{self.collection_name}' already exists. Skipping creation.")

        

    def insert(self, text, embedding):
        """
        Inserts a single document with its embedding.

        :param text: The original text.
        :param embedding: A list representing the embedding vector.
        """
        if len(embedding) != self.config.dimensions:
            raise ValueError(f"Embedding must be of dimension {self.config.dimensions}")

        doc = {"text": text, "text_embedding": embedding}
        self.collection.insert_one(doc)

    def batch_insert(self, documents):
        """
        Inserts multiple documents with embeddings.

        :param documents: A list of dictionaries with 'text' and 'vector' keys.
        """
        ic(len(documents[0]["text_embedding"]))
        ic(self.config.dimensions)
        for doc in documents:
            if len(doc["text_embedding"]) != self.config.dimensions:
                raise ValueError(f"Embedding must be of dimension {self.config.dimensions}")
        
        self.collection.insert_many(documents)

    def get(self, _id):
        """
        Retrieves a document by its ID.

        :param _id: The document ID.
        :return: The document.
        """
        return self.collection.find_one({"_id": _id})
    
    def find_one(self, query):
        """
        Retrieves a document based on a query.

        :param query: The query to use.
        :return: The document.
        """
        return self.collection.find_one(query)

    def query(self, pipeline): # XXX: to improve
        """
        Retrieves the top-k most similar documents based on text similarity.

        :param pipeline: The aggregation pipeline to use.
        :return: List of retrieved documents.
        """
        results = list(self.collection.aggregate(pipeline))
        return results

    def vector_search(self, vector, top_k=3):
        """
        Retrieves the top-k most similar documents based on vector similarity.

        :param query_embedding: A list representing the query embedding vector.
        :param top_k: Number of top similar documents to retrieve.
        :return: List of retrieved documents.
        """
        if len(vector) != self.config.dimensions:
            raise ValueError(f"Query embedding must be of dimension {self.config.dimensions}")

        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": vector,
                    "path": "text_embedding",
                    "numCandidates": 100,
                    "limit": top_k,
                    "index": "vector_index"
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))
        return results