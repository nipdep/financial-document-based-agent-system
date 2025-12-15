from typing import Any, Callable, Optional
from langchain.schema import Document
from langchain.embeddings.base import Embeddings

class BaseEmbedder:
    
    def __init__(self,  config):
        """
        Intialize the embedder class.

        :param config: embedder configuration option class, defaults to None
        :type config: Optional[BaseEmbedderConfig], optional
        """
        self.config = config

    def _create_client(self):
        """
        Create the client for the embedder.
        """
        raise NotImplementedError
    
    def embed(self, text: str) -> Any:
        """
        Generates an embedding for the given text.

        :param text: The input text (string).
        :return: A list of embedding values (float).
        """
        raise NotImplementedError
