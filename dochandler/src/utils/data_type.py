import os 
from typing import Any
from enum import Enum
from urllib.parse import urlparse

class DirectDataType(Enum):
    """
    DirectDataType enum contains data types that contain raw data directly.
    """

    TEXT = "text"

class IndirectDataType(Enum):
    """
    IndirectDataType enum contains data types that contain references to data stored elsewhere.
    """

    PDF_FILE = "pdf_file"
    DOCX = "docx"
    DOCS_SITE = "docs_site"
    CSV = "csv"
    MDX = "mdx"
    JSON = "json"
    WEB_PAGE = "web_page"


class SpecialDataType(Enum):
    """
    SpecialDataType enum contains data types that are neither direct nor indirect, or simply require special attention.
    """

    QNA_PAIR = "qna_pair"

class DataType(Enum):
    TEXT = DirectDataType.TEXT.value
    PDF_FILE = IndirectDataType.PDF_FILE.value
    DOCX = IndirectDataType.DOCX.value
    DOCS_SITE = IndirectDataType.DOCS_SITE.value
    CSV = IndirectDataType.CSV.value
    MDX = IndirectDataType.MDX.value
    QNA_PAIR = SpecialDataType.QNA_PAIR.value
    JSON = IndirectDataType.JSON.value
    WEB_PAGE = IndirectDataType.WEB_PAGE.value


def detect_datatype(source: Any) -> DataType:
    """
    Automatically detect the datatype of the given source.

    :param source: the source to base the detection on
    :return: data_type string
    """
    
    try:
        if not isinstance(source, str):
            raise ValueError(
                "Source is not a string and thus cannot be a URL.")
        url = urlparse(source)
        # Check if both scheme and netloc are present. Local file system URIs are acceptable too.
        if not all([url.scheme, url.netloc]) and url.scheme != "file":
            raise ValueError("Not a valid URL.")
    except ValueError:
        url = False

    if url:
        if url.path.endswith(".pdf"):
            return DataType.PDF_FILE
        elif url.path.endswith(".csv"):
            return DataType.CSV
        elif url.path.endswith(".docx"):
            return DataType.DOCX
        elif url.path.endswith(".json"):
            return DataType.JSON
        elif "docs" in url.netloc or ("docs" in url.path and url.scheme != "file"):
            return DataType.DOCS_SITE
        else:
            return DataType.WEB_PAGE
    elif os.path.isfile(source):
        if source.endswith(".docx"):
            return DataType.DOCX
        elif source.endswith(".csv"):
            return DataType.CSV
        elif source.endswith(".json"):
            return DataType.JSON
        elif source.endswith(".pdf"):
            return DataType.PDF_FILE
        elif source.endswith(".html"):
            return DataType.WEB_PAGE
        else:
            return DataType.TEXT
    else:
        return DataType.TEXT