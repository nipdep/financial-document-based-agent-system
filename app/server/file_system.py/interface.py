from .gridfs import GridFS

class FS:
    def __new__(self, db_type, **kwargs):
        self.__create_concrete__(self, db_type, **kwargs)
        return self._cls_concrete

    def __create_concrete__(self, db_type, **kwargs):
        if db_type == "mongo":
            self._cls_concrete = GridFS(**kwargs)
        else:
            raise NotImplementedError(f"DB type '{db_type}' is not implemented")