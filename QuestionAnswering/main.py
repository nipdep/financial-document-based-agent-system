from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_classic.memory import ConversationBufferWindowMemory

from QuestionAnswering.src.agent.generator import Generator
from QuestionAnswering.src.agent.retriever import Retriever
from dochandler.src.agent.judge import Judge
from cgcore.helper.json_serializable import register_deserializable

from cgcore.utils.utils import paragraph_list_to_str 

from icecream import ic

@register_deserializable
class ExTrRAGQA():
    def __init__(self, llm, db, embedder, memory="window_buffer", history=False):
        """
        Initialize the QA System.
        Notice: We do NOT need the Loader here. Only LLM, DB, and Embedder.
        """
        self.llm = llm
        self.db = db
        self.embedder = embedder
        self.memory_type = memory
        if history:
            self.history = []

        self._setup()
        
    def _setup(self):
        class Rule(BaseModel): 
            decision: bool = Field(description="Do you have all the required information to answer the query? in the provided context")
            related_context: str = Field(description="In any case of the decision, give the important information from the context to answer the query. Without any alteration. **if the context is empty, then just return empty string**")
            extra_questions: List[str] = Field(description="When the current context is not enough to answer the query, provide the extra questions to extract information that can help to answer the query.")
        
        judge_template = """
            Use the following pieces of context to answer the query at the end.
            Context: $context
            Query: $query
            Helpful Answer:
            """ 
        self.judge = Judge(llm=self.llm, rule=Rule, prompt_template=judge_template)

       
        self.context = ConversationBufferWindowMemory(k=5) 

        self.retriever = Retriever(db=self.db, embedder=self.embedder)

        gen_template = """
            Use the following pieces of context to answer the query at the end.
            Context: $context
            Query: $query
            Helpful Answer:
            """
        system_prompt = "You are an retrieval oriented chatbot. You are asked to provide an answer based on the context provided."
        
        self.generator = Generator(
            llm=self.llm, 
            memory_type=self.memory_type, 
            prompt_template=gen_template, 
            system_prompt=system_prompt
        )

    def chat(self, input_query: str):
        current_context = self.context.load_memory_variables({})['history']
        ic(f"Current Context: {current_context}")

        ruling = self.judge.judge_with_context(input_query, context=current_context)
        ic(ruling)
        
        related_context = ruling.related_context
        
        if ruling.decision:
            print("Decision: Sufficient context found in memory.")
            response = self.generator.generate_with_context(input_query, related_context)
        else:
            print("Decision: Retrieving external documents...")
            extra_questions = ruling.extra_questions
            
            if len(extra_questions) > 0:
                question_prompt = ", ".join(extra_questions)
            else:
                question_prompt = input_query
            
            related_docs = self.retriever.simple_retrieve(question_prompt)
            updated_docs = [{k: v for k, v in r.items() if k != "vector"} for r in related_docs]
            ic(updated_docs)

            if related_docs:
                new_content = [d['content'] for d in related_docs]
            else:
                new_content = ""
            
            updated_context = related_context + paragraph_list_to_str(new_content)
            response = self.generator.generate_with_context(input_query, updated_context)
            
        return response