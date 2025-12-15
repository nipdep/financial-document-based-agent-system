
from chatgenie.rag.base import BaseRAG
from chatgenie.config.rag.base import GeneralRAGConfig
from chatgenie.utils.utils import paragraph_list_to_str
from chatgenie.helper.json_serializable import register_deserializable

from chatgenie.agent.generator import Generator
from chatgenie.agent.retriever import Retriever
from chatgenie.agent.loader import Loader

@register_deserializable
class GeneralRAG(BaseRAG):
    def __init__(self, llm, db, embedder, memory="none", history=False):
        # config = GeneralRAGConfig(**kwargs)
        # super().__init__(llm, db, embedder, **kwargs)
        self.llm = llm
        self.db = db
        self.embedder = embedder
        self.memory = memory
        if history:
            self.history = []

        self._setup()
        
    def _setup(self):
        self.loader = Loader(db=self.db, embedder=self.embedder)
        self.retriever = Retriever(db=self.db, embedder=self.embedder)
        prompt_template = """
            Use the following pieces of context to answer the query at the end.
            If the question is not related to obesity or weight-loss, just say that you don't know, don't try to make up an answer.
            I will provide you with our conversation history.

            $context

            History: $history

            Query: $query

            Helpful Answer:
            """
        system_prompt = "You are an retrieval oriented chatbot. You are asked to provide an answer based on the context provided."  
        self.generator = Generator(llm=self.llm, memory_type=self.memory, memory_size=2, prompt_template=prompt_template, system_prompt=system_prompt)

    def chat(self, input_query):
        # get context
        context_docs = self.retriever.simple_retrieve(input_query)
        if context_docs:
            context_str = [d['content'] for d in context_docs]
            context = paragraph_list_to_str(context_str)
        else:
            context = ""
        # get response
        response = self.generator.generate_with_context(input_query, context)
        return response
    
    def add_document(self, source, metadata={}):
        try:
            self.loader.simple_load(source, metadata)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
