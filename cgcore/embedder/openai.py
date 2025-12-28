from typing import Optional

from langchain_openai import OpenAIEmbeddings
from cgcore.embedder.base import BaseEmbedder


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, config):
        super().__init__(config)
        self._create_client()

    def _create_client(self):
        self.embedder = OpenAIEmbeddings(
            api_key=self.config.api_key,
            model= self.config.model_name,
            encoding_format= self.config.encoding_format,
            dimensions= self.config.dimensions
        )
        
    def embed(self, text: str) -> Optional[list]:
        """
        Generates an embedding for the given text.

        :param text: The input text (string).
        :return: A list of embedding values (float).
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text must be a non-empty string.")

        # Generate embeddings
        return self.embedder.embed_query(text)
  