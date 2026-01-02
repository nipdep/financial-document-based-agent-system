from typing import Optional
from cgcore.configs.embedder.base import BaseEmbedderConfig

class OpenAIEmbedderConfig(BaseEmbedderConfig):
    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = "text-embedding-ada-002",
        encoding_format: Optional[str] = None,
        dimensions: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(api_key=api_key, model_name=model_name, encoding_format=encoding_format, dimensions=dimensions, **kwargs)
