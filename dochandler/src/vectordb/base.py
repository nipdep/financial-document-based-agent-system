class BaseVectorDB:
    """Base class for vector database."""

    def __init__(self, config):
        """
        Initialize the database based on the selected type.

        :param db_type: The type of vector database (mongo, chroma, pinecone, etc.)
        :param config: Database configuration instance (optional)
        """
        self.config = config

    def _create_client(self):
        """
        Create the client for the database.
        """
        raise NotImplementedError

    def _create_collection(self):
        """
        Create the collection for the database.
        """
        raise NotImplementedError
    
    def insert(self, text, embedding, **kwargs):
        """
        Insert a document into the database.

        :param text: The text to insert
        :param embedding: The embedding to insert
        """
        raise NotImplementedError
    
    def batch_insert(self, text, embedding, **kwargs):
        """
        Insert multiple documents into the database.

        :param texts: The texts to insert
        :param embeddings: The embeddings to insert
        """
        raise NotImplementedError
    
    def get(self, _id):
        """
        Get a document from the database.

        :param _id: The ID of the document to retrieve
        """
        raise NotImplementedError
    
    def find_one(self, query):
        """
        Find a document in the database.

        :param
        """
        raise NotImplementedError
    
    def query(self, pipeline):
        """
        Query the database for similar documents.

        :param query: The query to use
        :param top_k: The number of similar documents to return
        """
        raise NotImplementedError
    
    def vector_search(self, query, top_k=3):
        """
        Search the database for similar vectors.

        :param query: The query to use
        :param top_k: The number of similar vectors to return
        """
        raise NotImplementedError
