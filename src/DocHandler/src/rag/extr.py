from pydantic import BaseModel, Field
from typing import List
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory

from chatgenie.rag.base import BaseRAG
from chatgenie.config.rag.base import GeneralRAGConfig
from chatgenie.utils.utils import paragraph_list_to_str
from chatgenie.helper.json_serializable import register_deserializable

from chatgenie.agent.generator import Generator
from chatgenie.agent.retriever import Retriever
from chatgenie.agent.loader import Loader
from chatgenie.agent.judge import Judge

from icecream import ic

@register_deserializable
class ExTrRAG(BaseRAG):
    def __init__(self, llm, db, embedder, memory="none", history=False):
        self.llm = llm
        self.db = db
        self.embedder = embedder
        self.memory = memory
        if history:
            self.history = []

        self._setup()
        
    def _setup(self):
        # create question generator agent 
        class Questions(BaseModel): # XXX: need to improve
            questions: List[str] = Field(description="3 The questions related to the paragraph")
        question_generator = Judge(llm=self.llm, rule=Questions)
        # build the document loader 
        self.loader = Loader(db=self.db, embedder=self.embedder, llm=question_generator)
        # loader.extr_load(source="data/obesity.txt")

        # building judge agent 
        class Rule(BaseModel): # XXX: need to improve
            decision: bool = Field(description="Do you have all the required information to answer the query? in the provided context")
            related_context: str = Field(description="In any case of the decision, give the important information from the context to answer the query. Without any alteration. **if the context is empty, then just return empty string**")
            extra_questions: List[str] = Field(description="When the current context is not enough to answer the query, provide the extra questions to extract information that can help to answer the query.")
        prompt_template = """
            Use the following pieces of context to answer the query at the end.

            Context: $context

            Query: $query

            Helpful Answer:
            """ 
        self.judge = Judge(llm=self.llm, rule=Rule, prompt_template=prompt_template)


        self.context = ConversationBufferWindowMemory(k=5) # XXX: memory vs. context size 

        # building retriever agent 
        self.retriever = Retriever(db=self.db, embedder=self.embedder, llm=question_generator)

        # building generator agent
        prompt_template = """
            Use the following pieces of context to answer the query at the end.

            Context: $context

            Query: $query

            Helpful Answer:
            """
        system_prompt = "You are an retrieval oriented chatbot. You are asked to provide an answer based on the context provided."
        self.generator = Generator(llm=self.llm, memory_type="none", prompt_template=prompt_template, system_prompt=system_prompt)

    def chat(self, input_query):
        # chech with judge first 
        current_context = self.context.load_memory_variables({})['history']
        ic(current_context)
        ruling = self.judge.judge_with_context(input_query, context=current_context) # XXX: need to add context
        ic(ruling)
        related_context = ruling.related_context
        if ruling.decision:
            response = self.generator.generate_with_context(input_query, related_context)
        else:
            extra_questions = ruling.extra_questions
            if len(extra_questions) > 0:
                question_prompt = ", ".join(extra_questions)
            else:
                question_prompt = input_query
            related_docs = self.retriever.simple_retrieve(question_prompt)

            updated_docs = [{k: v for k, v in r.items() if k != "text_embedding"} for r in related_docs]
            ic(updated_docs)

            if related_docs:
                new_context = [d['content'] for d in related_docs]
            else:
                new_context = ""
            updated_context = related_context + paragraph_list_to_str(new_context)
            ic(updated_context)
            response = self.generator.generate_with_context(input_query, updated_context)
        return response
    
    def add_document(self, source, metadata={}):
        self.loader.extr_load(source, metadata)
        # try:
        #     self.loader.extr_load(source, metadata)
        #     return True
        # except Exception as e:
        #     return False