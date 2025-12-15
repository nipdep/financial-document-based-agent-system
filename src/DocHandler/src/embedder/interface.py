import os
from typing import Optional, Type
from enum import Enum
from chatgenie.embedder.base import BaseEmbedder

class Embedder:
    def __new__(self, embedder_type,**kwargs):
        self.__create_concrete__(self, embedder_type,**kwargs)
        return self._cls_concrete
    
    def __create_concrete__(self, embedder_type,**kwargs):
        if embedder_type == "openai":
            from chatgenie.embedder.openai import OpenAIEmbedder
            from chatgenie.config.embedder.openai import OpenAIEmbedderConfig
            config = OpenAIEmbedderConfig(**kwargs)
            self._cls_concrete = OpenAIEmbedder(config)
        else:
            raise NotImplementedError