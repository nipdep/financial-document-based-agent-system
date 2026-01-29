from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_classic.memory import ConversationBufferWindowMemory

from src.finchat.src.agent.generator import Generator
from src.finchat.src.agent.retriever import Retriever
from src.dochandler.src.agent.judge import Judge
from src.cgcore.helper.json_serializable import register_deserializable
from src.cgcore.utils.utils import format_docs_with_citations
import asyncio
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
            You are a helpful assistant. Use the following context documents to answer the query.
            
            The context is provided inside <document> tags. Each document has a specific index (e.g., [1]).
            
            RULES:
            1. You must answer the query using ONLY the provided documents.
            2. When you state a fact, you MUST cite the source index using square brackets like [1] or [1][2].
            3. If the answer is not in the documents, state that you do not know.
            
            Context:
            $context
            
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

    async def chat(self, input_query: str):
        current_context = self.context.load_memory_variables({})['history']
        ic(f"Current Context: {current_context}")

        ruling = await self.judge.judge_with_context(input_query, context=current_context)
        ic(ruling)
        
        related_context = ruling.related_context
        sources_to_return = []
        if ruling.decision:
            print("Decision: Sufficient context found in memory.")
            response = await self.generator.generate_with_context(input_query, related_context)
        else:
            print("Decision: Retrieving external documents...")
            extra_questions = ruling.extra_questions
            
            if len(extra_questions) > 0:
                question_prompt = ", ".join(extra_questions)
            else:
                question_prompt = input_query
            
            # 1. Get the docs
            related_docs = await self.retriever.simple_retrieve(question_prompt)
            updated_docs = [{k: v for k, v in r.items() if k != "vector"} for r in related_docs]
            ic(updated_docs)


            # We pass 'updated_docs' (the full dictionaries) so the formatter can see filenames
            if updated_docs:
                new_context_str = format_docs_with_citations(updated_docs)
            else:
                new_context_str = ""
                
            for i, doc in enumerate(updated_docs):
                    
                   
                    real_db_id = doc.get('_id')
                    
                    sources_to_return.append({
                        "citation_index": i + 1,        
                        "chunk_id": str(real_db_id),                         
                        "filename": doc.get('metadata', {}).get('original_filename', 'Unknown'),
                        "content": doc.get('content', '')
                    })

            updated_context = f"{related_context}\n\n{new_context_str}"
            response_text = await self.generator.generate_with_context(input_query, updated_context)
            
        return {
            "answer": response_text,
            "sources": sources_to_return
        }