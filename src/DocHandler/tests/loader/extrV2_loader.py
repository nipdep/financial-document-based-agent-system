import os
import unittest
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import chatgenie as cg
from chatgenie.resources.transformations.clustering.density_base_cluster import DensityBasedCluster
from dotenv import load_dotenv
import requests

def download_pdf(url, filename):
    response = requests.get(url, stream=True)  # Stream the response for large files
    response.raise_for_status()  # Raise error for failed requests

    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
            file.write(chunk)

    print(f"PDF downloaded successfully: {filename}")



class TestCGExTrLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Runs once before all tests """
        cls.root_path = Path(__file__).resolve().parent.parent.parent
        print(cls.root_path)
        path_to_env = os.path.join(
            cls.root_path,
            ".env"
        )
        load_dotenv(dotenv_path=path_to_env)
        
        # load data
        cls.data_path = os.path.join(
            cls.root_path,
            "data"
        )
        
        if not os.path.exists(
            os.path.join(
                cls.data_path, 
                "Easy_recipes.pdf")
            ):
            os.makedirs(cls.data_path, exist_ok=True)
            download_pdf(
                'https://www.bu.edu/geneva/files/2010/08/Easy_recipes.pdf', 
                os.path.join(cls.data_path, "Easy_recipes.pdf")
            )
            
        # Get secrets
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        DB_USERNAME = os.getenv("DB_USERNAME")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_COLLECTION = os.getenv("DB_COLLECTION")
        DB_APP_NAME = os.getenv("DB_APP_NAME")
        DB_NAME = os.getenv("DB_NAME")
        DB_DIMENSION = os.getenv("MONGO_DB_DIMENSION", 1536)
        
        # building base units
        cls.llm = cg.LLM(llm_type='openai', api_key=OPENAI_API_KEY)

        cls.embedder = cg.Embedder(
            embedder_type='openai', 
            api_key=OPENAI_API_KEY,
            model='text-davinci-003', 
            dimesion=DB_DIMENSION)

        cls.vector_db = cg.VectorDB(
            db_type="mongo",
            username=DB_USERNAME,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            collection_name=DB_COLLECTION,
            app_name=DB_APP_NAME,
            dimensions=DB_DIMENSION
        )
        
        cls.cluster = DensityBasedCluster(
            obj_location=os.path.join(
                cls.data_path, 
                "Easy_recipes_cluster.pkl"
                )
            )
        
        cls.extr_rag = cg.ExTrRAGV2(
                llm=cls.llm,
                embedder=cls.embedder,
                db=cls.vector_db,
                cluster=cls.cluster,
                memory="none",
                history=True,
            )
        
        # building pipeline
        
        
    @classmethod
    def tearDownClass(cls):
        """ Runs once after all tests """
        cls.vector_db.client.close()
    
    #def test_simple_load(self):
    #    self.loader.simple_load(
    #        source=os.path.join(
    #            self.data_path, 
    #            "Easy_recipes.pdf"
    #            )
    #        )
    
    #def test_extr_cluster_load(self):
    #    self.extr_rag.loader.extr_cluster_load(
    #        source=os.path.join(
    #                self.data_path, 
    #                "Easy_recipes.pdf"
    #                ),
    #        cluster=self.cluster,
    #    )
        
    #    self.cluster.fit()
    #    self.cluster.serialize()
    
    def test_extr_cluster_chat(self):
        self.extr_rag.chat(
            "Give me a set of dishes that I can create with chicken and rice?"
            )

if __name__ == '__main__':
    unittest.main()