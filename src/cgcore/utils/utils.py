import re
from typing import List
from urllib.parse import urlparse
import os
import string
import logging
from typing import List, Dict

def format_source(source: str, limit: int = 20) -> str:
    """
    Format a string to only take the first x and last x letters.
    This makes it easier to display a URL, keeping familiarity while ensuring a consistent length.
    If the string is too short, it is not sliced.
    """
    if len(source) > 2 * limit:
        return source[:limit] + "..." + source[-limit:]
    return source

def clean_string(text):
    """
    This function takes in a string and performs a series of text cleaning operations.

    Args:
        text (str): The text to be cleaned. This is expected to be a string.

    Returns:
        cleaned_text (str): The cleaned text after all the cleaning operations
        have been performed.
    """
    # Replacement of newline characters:
    text = text.replace("\n", " ")

    # Stripping and reducing multiple spaces to single:
    cleaned_text = re.sub(r"\s+", " ", text.strip())

    # Removing backslashes:
    cleaned_text = cleaned_text.replace("\\", "")

    # Replacing hash characters:
    cleaned_text = cleaned_text.replace("#", " ")

    # Eliminating consecutive non-alphanumeric characters:
    # This regex identifies consecutive non-alphanumeric characters (i.e., not
    # a word character [a-zA-Z0-9_] and not a whitespace) in the string
    # and replaces each group of such characters with a single occurrence of
    # that character.
    # For example, "!!! hello !!!" would become "! hello !".
    cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)

    return cleaned_text


def is_readable(s):
    """
    Heuristic to determine if a string is "readable" (mostly contains printable characters and forms meaningful words)

    :param s: string
    :return: True if the string is more than 95% printable.
    """
    try:
        printable_ratio = sum(c in string.printable for c in s) / len(s)
    except ZeroDivisionError:
        logging.warning("Empty string processed as unreadable")
        printable_ratio = 0
    return printable_ratio > 0.95  # 95% of characters are printable


def paragraph_list_to_str(paragraph_list: List[str]) -> str:
    return "\n".join(paragraph_list)


def format_docs_with_citations(docs: List[Dict]) -> str:
    """
    Turns a list of docs into an XML-like string for the LLM.
    Example Output:
    <document index="1">
    Content: The net profit was $500.
    Source: report.pdf
    </document>
    """
    formatted_str = ""
    for i, doc in enumerate(docs):
        # We use i+1 so the citations start at [1] instead of [0]
        content = doc.get('content', '').strip()
        source_name = doc.get('metadata', {}).get('original_filename', 'Unknown')
        
        formatted_str += f"""<document index="{i+1}">
        Content: {content}
        Source: {source_name}
        </document>\n\n"""
                
    return formatted_str


def is_url(path):
    """
    Checks if a given path is a URL.
    
    A path is considered a URL if it has a scheme (e.g., 'http', 'https')
    and a network location (e.g., 'www.example.com').
    
    Args:
        path (str): The path string to check.
        
    Returns:
        bool: True if the path is a URL, False otherwise.
    """
    if not isinstance(path, str):
        return False
    try:
        result = urlparse(path)
        # A URL must have a scheme and a netloc
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_local_path(path):
    """
    Checks if a given path is a local file path.
    
    This function checks for URL characteristics first and also verifies
    if the path exists on the local filesystem for confirmation.
    
    Args:
        path (str): The path string to check.
        
    Returns:
        bool: True if the path is a local path, False otherwise.
    """
    if is_url(path):
        return False
    
    # Check if it's a valid path format for the OS and/or if it exists.
    # os.path.exists is a strong indicator for existing local paths.
    # An absolute path is also a strong indicator.
    return os.path.exists(path) or os.path.isabs(path)