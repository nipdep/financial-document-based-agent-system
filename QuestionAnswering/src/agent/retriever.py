from typing import Optional

from cgcore.llm.base import BaseLlm
from cgcore.embedder.base import BaseEmbedder
from cgcore.vectordb.base import BaseVectorDB
from cgcore.utils.utils import paragraph_list_to_str
from QuestionAnswering.src.resources.transformations.clustering.density_base_cluster import DensityBasedCluster

from icecream import ic

class Retriever:
    def __init__(self,
                 db: BaseVectorDB,
                 embedder: BaseEmbedder,
                 llm: Optional[BaseLlm]=None):
        self.db = db
        self.embedder = embedder
        self.llm = llm

    def simple_retrieve(self, prompt: str) -> str:
        input_query_embedding = self.embedder.embed(prompt)
        relevant_docs = self.db.vector_search(input_query_embedding)
        return relevant_docs
    
    def extr_cluster_retrieve(self, prompt: str, cluster:DensityBasedCluster) -> str:
        input_query_embedding = self.embedder.embed(prompt)
        cluster.fit(force=True)
        _ids_info = cluster.get_cluster_ids(input_query_embedding)
        relevant_docs = []
        for _id in _ids_info:
            doc = self.db.find_one({"chunk_id": _id["chunk_id"]})
            doc["retrieve_count"] = _id["count"]
            doc["spawn_prompt"] = prompt
            relevant_docs.append(doc)
        return relevant_docs
    
        
    
