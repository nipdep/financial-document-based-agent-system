from typing import Optional, Callable

from langchain.text_splitter import RecursiveCharacterTextSplitter

from dochandler.src.chunkers.base_chunker import BaseChunker
from cgcore.configs.base_config import BaseConfig

class ChunkerConfig(BaseConfig):
    """
    Config for the chunker used in `add` method
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        length_function: Optional[Callable[[str], int]] = None,
    ):
        self.chunk_size = chunk_size if chunk_size else 2000
        self.chunk_overlap = chunk_overlap if chunk_overlap else 0
        self.length_function = length_function if length_function else len

class PdfFileChunker(BaseChunker):
    """Chunker for PDF file."""

    def __init__(self, config: Optional[ChunkerConfig] = None):
        if config is None:
            config = ChunkerConfig(
                chunk_size=1000, chunk_overlap=0, length_function=len)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=config.length_function,
        )
        super().__init__(text_splitter)
