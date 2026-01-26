from importlib import import_module

from cgcore.configs.add_config import AddConfig
from cgcore.configs.add_config import ChunkerConfig, LoaderConfig
from cgcore.utils.data_type import DataType

from dochandler.src.chunkers.base_chunker import BaseChunker
from dochandler.src.loader.base_loader import BaseLoader
from dochandler.src.loader.pdf_file import PdfFileLoader 

class DataFormatter:
    """
    DataFormatter is an internal utility class which abstracts the mapping for
    loaders and chunkers to the data_type entered by the user in their
    .add or .add_local method call
    """

    def __init__(self, data_type: DataType, config: AddConfig):
        """
        Initialize a dataformatter, set data type and chunker based on datatype.

        :param data_type: The type of the data to load and chunk.
        :type data_type: DataType
        :param config: AddConfig instance with nested loader and chunker config attributes.
        :type config: AddConfig
        """
        self.loader = self._get_loader(
            data_type=data_type, config=config.loader)
        self.chunker = self._get_chunker(
            data_type=data_type, config=config.chunker)

    def _lazy_load(self, module_path: str):
        module_path, class_name = module_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, class_name)

    def _get_loader(self, data_type: DataType, config: LoaderConfig) -> BaseLoader:
        """
        Returns the appropriate data loader for the given data type.

        :param data_type: The type of the data to load.
        :type data_type: DataType
        :param config: Config to initialize the loader with.
        :type config: LoaderConfig
        :raises ValueError: If an unsupported data type is provided.
        :return: The loader for the given data type.
        :rtype: BaseLoader
        """
        loaders = {
            DataType.PDF_FILE: "dochandler.src.loader.pdf_file.PdfFileLoader",
            DataType.QNA_PAIR: "chatgenie.loaders.local_qna_pair.LocalQnaPairLoader",
            DataType.TEXT: "chatgenie.loaders.local_text.LocalTextLoader",
            DataType.DOCX: "chatgenie.loaders.docx_file.DocxFileLoader",
            DataType.DOCS_SITE: "chatgenie.loaders.docs_site_loader.DocsSiteLoader",
            DataType.CSV: "chatgenie.loaders.csv.CsvLoader",
            DataType.MDX: "chatgenie.loaders.mdx.MdxLoader",
            DataType.JSON: "chatgenie.loaders.json.JSONLoader"
        }
        if data_type in loaders:
            loader_class: type = self._lazy_load(loaders[data_type])
            return loader_class(config)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def _get_chunker(self, data_type: DataType, config: ChunkerConfig) -> BaseChunker:
        """Returns the appropriate chunker for the given data type (updated for lazy loading)."""
        chunker_classes = {
            DataType.PDF_FILE: "dochandler.src.chunkers.mdx.MdxChunker",
            DataType.QNA_PAIR: "chatgenie.chunkers.qna_pair.QnaPairChunker",
            DataType.TEXT: "chatgenie.chunkers.text.TextChunker",
            DataType.DOCX: "chatgenie.chunkers.docx_file.DocxFileChunker",
            DataType.DOCS_SITE: "chatgenie.chunkers.docs_site.DocsSiteChunker",
            DataType.CSV: "chatgenie.chunkers.table.TableChunker",
            DataType.MDX: "chatgenie.chunkers.mdx.MdxChunker",
            DataType.JSON: "chatgenie.chunkers.json.JSONChunker"
        }

        if data_type in chunker_classes:
            chunker_class = self._lazy_load(chunker_classes[data_type])
            chunker = chunker_class(config)
            chunker.set_data_type(data_type)
            return chunker
        else:
            raise ValueError(f"Unsupported data type: {data_type}")