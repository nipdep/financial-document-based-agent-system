from typing import Dict, Optional, List
from pydantic import BaseModel, Field

from cgcore.vectordb.base import BaseVectorDB
from cgcore.embedder.base import BaseEmbedder
from cgcore.llm.base import BaseLlm
from cgcore.configs.add_config import AddConfig
from dochandler.src.utils.data_formatter import DataFormatter
from cgcore.utils.data_type import detect_datatype

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
            self.db.insert(records)
        else:
            return records

    def extr_load(self, source: str, metadata: Optional[Dict] = {}):
        data_type = detect_datatype(source)

        data_formatter = DataFormatter(data_type, self.config)
        chunks = data_formatter.chunker.create_chunks(data_formatter.loader, source)
        doc_id = chunks.get("doc_id", "unknown_id")
        records = []
        for i, chunk_id in enumerate(chunks["ids"]):
            content = chunks["documents"][i]
            question_response = self.llm.judge(content)
            questions = question_response.questions
            ic(questions)
            final_metadata = chunks["metadatas"][i].copy()
            final_metadata.update(metadata)
            final_metadata["original_chunk_id"] = chunk_id
            
            if len(questions) > 0:
                for q in questions:
                    embedding = self.embedder.embed(q)
                    final_metadata["question"] = q
                    records.append(
                        {
                            "doc_id":         doc_id,           
                            "vector":         embedding,        
                            "content":        content,          
                            "meta_data":      final_metadata    
                        }
                    )
                    
            else:
                embedding = self.embedder.embed(content)
                final_metadata["questions"] = None
                records.append(
                    {
                        "doc_id":         doc_id,           
                        "vector":         embedding,        
                        "content":        content,          
                        "meta_data":      final_metadata    
                    }
                )

        if not self.dry_run:
            success=self.db.insert(records)
            if success:
                print(f"Successfully inserted {len(records)} records into Milvus.")
            else:
                print(f"Failed to insert records. Check Milvus logs above.")
        else:
            return records