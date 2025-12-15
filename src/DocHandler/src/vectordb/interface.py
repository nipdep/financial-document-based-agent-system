# vectorDB/interface.py


class VectorDB:
    def __new__(self, db_type, **kwargs):
        self.__create_concrete__(self, db_type, **kwargs)
        return self._cls_concrete

    def __create_concrete__(self, db_type, **kwargs):
        if db_type == "mongo":
            from chatgenie.vectordb.mongo import MongoDB
            from chatgenie.config.vectordb.mongo import MongoConfig
            config = MongoConfig(**kwargs)
            self._cls_concrete = MongoDB(config)
        else:
            raise NotImplementedError(f"Vector DB type '{db_type}' is not implemented")
