import os
import unittest
from pathlib import Path
import chatgenie as cg
from dotenv import load_dotenv

class TestCGGeneralRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Runs once before all tests """
        path_to_env = os.path.join(
            Path(__file__).resolve().parent.parent,
            ".env"
        )
        load_dotenv(dotenv_path=path_to_env)
            
        # Get secrets
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        DB_USERNAME = os.getenv("DB_USERNAME")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_COLLECTION = os.getenv("DB_COLLECTION")
        DB_APP_NAME = os.getenv("DB_APP_NAME")
        DB_NAME = os.getenv("DB_NAME")
        
        # building base units
        cls.llm = cg.LLM(
            llm_type = cg.LLMTypes.OPENAI,
            template = cg.PromptTemplate.DEFAULT_PROMPT_WITH_HISTORY,
            model = "gpt-4o",
        )

        cls.embedder = cg.Embedder(
            embedder_type = cg.EmbedderTypes.OPENAI,
        )

        cls.vector_db = cg.VectorDB(
            db_type = cg.VectorDBTypes.MONGO,
            collection_name= DB_COLLECTION,
            username= DB_USERNAME,
            password= DB_PASSWORD,   
            app_name= DB_APP_NAME, 
            dbname= DB_NAME, 
            dimensions= 1536,
            allow_reset= True,
        )

        # building pipeline
        cls.agent = cg.agent.GeneralRAG(
            llm = cls.llm,
            embedder = cls.embedder,
            db = cls.vector_db,
            max_results = 5,
        )
        
        cls.communicator = cg.communicator.GeneralRAG(
            agent = cls.agent
        )
        
        cls.threadhandler = cg.thread_handler.DictThreadHandler(
            cls.communicator
        )
        
    @classmethod
    def tearDownClass(cls):
        """ Runs once after all tests """
        cls.vector_db.client.close()
    
    def test_retrieve_from_database(self):
        from chatgenie.data.query import QueryDataPacket
        db_result = self.agent.retrieve_from_database(
            QueryDataPacket(
                input_query = "Explore FitSmiles Community"
                )
            )
        self.assertEqual(len(db_result), 10)

    def test_query(self):
        from chatgenie.data.query import QueryDataPacket
        response = self.agent.query(
            QueryDataPacket(
                input_query = "Explore FitSmiles Community"
                )
            )
        
        self.assertTrue(isinstance(response, tuple))
        self.assertTrue(isinstance(response[0].input_query, str))
        self.assertTrue(isinstance(response[1], str))
        
    def test_communicator(self):
        response = self.communicator.query(
            "Explore FitSmiles Community"
            )
        
        self.assertTrue(isinstance(response, tuple))
        self.assertTrue(isinstance(response[0].input_query, str))
        self.assertTrue(isinstance(response[1], str))
    
    def test_threadhandler(self):
        response = self.threadhandler.request(
            "Explore FitSmiles Community",
            agent_id = None
            )
        
        self.assertTrue(isinstance(response, dict))
        self.assertTrue(isinstance(response['agent_id'], int))
        self.assertTrue(isinstance(response['request_text'], str))
        
        response = self.threadhandler.request(
            "What country is fitsmiles based on ?",
            agent_id = None
            )
        
        agent_id = response['agent_id']
        response = self.threadhandler.request(
            "What was my previous question about",
            agent_id = agent_id
            )
        
        print(response)
        self.assertTrue(isinstance(self.threadhandler.agent_dict, dict))
        self.assertTrue(len(self.threadhandler.agent_dict.keys()) == 2)

if __name__ == '__main__':
    unittest.main()