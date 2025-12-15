from typing import Dict, Optional, List
from pydantic import BaseModel, Field

from chatgenie.vectordb.base import BaseVectorDB
from chatgenie.embedder.base import BaseEmbedder
from chatgenie.llm.base import BaseLlm
from chatgenie.config.add_config import AddConfig
from chatgenie.utils.data_formatter import DataFormatter
from chatgenie.utils.data_type import detect_datatype
from chatgenie.resources.transformations.clustering.density_base_cluster import DensityBasedCluster

from icecream import ic

class Loader:
    def __init__(self, 
                db: BaseVectorDB,
                embedder: BaseEmbedder,
                llm: Optional[BaseLlm] = None,
                config: Optional[AddConfig] = AddConfig(),
                dry_run: Optional[bool] = False,
                ):
        self.db = db
        self.embedder = embedder
        self.llm = llm
        self.config = config
        self.dry_run = dry_run


    def simple_load(self, source: str, metadata: Optional[Dict] = {}):
        
        data_type = detect_datatype(source)

        data_formatter = DataFormatter(data_type, self.config)
        chunks = data_formatter.chunker.create_chunks(data_formatter.loader, source)    

        records = []
        for i, chunk_id in enumerate(chunks["ids"]):
            records.append(
                {
                    "_id": chunk_id,
                    "content": chunks["documents"][i],
                    "meta_data": chunks["metadatas"][i] | metadata,
                    "text_embedding": self.embedder.embed(chunks["documents"][i])
                }
            )

        # TODO: check for existing records add only new records
        

        if not self.dry_run:
            self.db.batch_insert(records)
        else:
            return records

    def extr_load(self, source: str, metadata: Optional[Dict] = {}):
        data_type = detect_datatype(source)

        data_formatter = DataFormatter(data_type, self.config)
        chunks = data_formatter.chunker.create_chunks(data_formatter.loader, source)

        records = []
        for i, chunk_id in enumerate(chunks["ids"]):
            content = chunks["documents"][i]
            question_response = self.llm.judge(content)

            questions = question_response.questions
            if len(questions) > 0:
                embedding = self.embedder.embed(", ".join(questions))
            else:
                embedding = self.embedder.embed(content)
            records.append(
                {
                    "_id": chunk_id,
                    "content": content,
                    "questions": questions,
                    "meta_data": chunks["metadatas"][i] | metadata,
                    "text_embedding": embedding
                }
            )

        if not self.dry_run:
            self.db.batch_insert(records)
        else:
            return records
        
    def extr_cluster_load(self, source: str, cluster:DensityBasedCluster, metadata: Optional[Dict] = {}):
        data_type = detect_datatype(source)

        data_formatter = DataFormatter(data_type, self.config)
        chunks = data_formatter.chunker.create_chunks(data_formatter.loader, source)

        records = []
        for i, chunk_id in enumerate(chunks["ids"]):
            content = chunks["documents"][i]
            question_response = self.llm.judge(content)

            questions = question_response.questions
            
            if len(questions) > 0:
                for question in questions:
                    embedding = self.embedder.embed(question)
                    unq_id = cluster.update_db_index(chunk_id, question, embedding)
                    records.append(
                        {
                            "_id": unq_id,
                            "chunk_id": chunk_id,
                            "content": content,
                            "questions": question,
                            "meta_data": chunks["metadatas"][i] | metadata,
                            "text_embedding": embedding
                        }
                    )
                    
                    
            else:
                embedding = self.embedder.embed(content)
                unq_id = cluster.update_db_index(chunk_id, question, embedding)
                records.append(
                        {
                            "_id": unq_id,
                            "chunk_id": chunk_id,
                            "content": content,
                            "questions": question,
                            "meta_data": chunks["metadatas"][i] | metadata,
                            "text_embedding": embedding
                        }
                    )
            

        if not self.dry_run:
            self.db.batch_insert(records)
        else:
            return records 
    

        