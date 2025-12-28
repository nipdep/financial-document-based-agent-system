import re
from string import Template


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
            if history_re.search(prompt_template) is not None:
                return template.substitute(query=query, history=history)
            else:
                return template.substitute(query=query)
    else:
        # return error 
        raise ValueError("Template is not valid")
    
def answer_type_mapper(answer_type: str) -> str:
    mapper = {
        "general": "Provide a helpful and concise answer to the question.",
        "long_description": "Provide a comprehensive and detailed answer. Your response should be a well-structured, multi-paragraph analysis that explores the nuances of the topic, drawing deeply from the provided context.",
        "short_description": "Generate a brief and concise summary. The answer should be two to three sentences long, capturing the main points from the context without going into excessive detail.",
        "code_snippet": "Provide a complete code snippet that addresses the query. Ensure that the code is well-commented and easy to understand, and that it directly relates to the question asked.",
        "oneliner": "You must respond in one single, direct sentence. Provide only the factual answer found in the context, with no extra explanations or introductory phrases.",
        "bulleted_points": "Extract the key takeaways or features from the context and present them as a clear, concise bulleted list. Each bullet point should cover a distinct idea. Begin the list immediately.",
        "numberd_steps": "Create a set of step-by-step instructions to address the user's question. The output must be a numbered list where each step is a clear, actionable instruction. Begin the list immediately.",
        "table_format": "Organize the relevant information into a markdown table. Identify the appropriate columns and rows based on the context to create a structured comparison or data layout.",
        "json_object": "Format the response as a valid JSON object. Extract the key details from the context and structure them within the JSON. For example: {'summary': '...', 'key_data': [...]}.",
        "pros_and_cons": "Analyze the context to create a balanced list of pros and cons related to the user's question. Present the output with two distinct sections: 'Pros' and 'Cons,' each with bulleted points."
    }

    if mapper.get(answer_type):
        return mapper[answer_type]
    else:
        return mapper["general"]  # default to general if not found
    
    

    