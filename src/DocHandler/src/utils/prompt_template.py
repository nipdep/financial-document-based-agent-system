import re
from string import Template
from enum import Enum


DEFAULT_PROMPT = """
  Use the following pieces of context to answer the query at the end.

  $context

  Query: $query

  Helpful Answer:
""" 

DEFAULT_PROMPT_WITH_HISTORY = """
  Use the following pieces of context to answer the query at the end.
  If the question is not related to obesity or weight-loss, just say that you don't know, don't try to make up an answer.
  I will provide you with our conversation history.

  $context

  History: $history

  Query: $query

  Helpful Answer:
"""  

DOCS_SITE_DEFAULT_PROMPT = """
  Use the following pieces of context to answer the query at the end.
  If you don't know the answer, just say that you don't know, don't try to make up an answer. Wherever possible, give complete code snippet. Dont make up any code snippet on your own.

  $context

  Query: $query

  Helpful Answer:
"""  
    
def fill_template(prompt_template: str, query: str, context: str="", history: str="") -> str:
    template = Template(prompt_template)
    query_re = re.compile(r"\$\{*query\}*")
    context_re = re.compile(r"\$\{*context\}*")
    history_re = re.compile(r"\$\{*history\}*")

    if query_re.search(prompt_template) is not None:
        if context_re.search(prompt_template) is not None:
            if history_re.search(prompt_template) is not None:
                return template.substitute(query=query, context=context, history=history)
            else:
                return template.substitute(query=query, context=context)
        else:
            return template.substitute(query=query)
    else:
        # return error 
        raise ValueError("Template is not valid")

    