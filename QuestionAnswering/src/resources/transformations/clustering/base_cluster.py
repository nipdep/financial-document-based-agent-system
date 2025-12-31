
from enum import Enum
import os
import hashlib
import numpy as np
import pickle
from cgcore.vectordb.base import BaseVectorDB

class MemoryUnit:
    pass
    
class ClusterTypes(Enum):
    OPTICS = "OPTICS"
    DBSCAN = "DBSCAN"
    SOM = "SOM"
    
def if_available_deserialize(cls):
    def get_instance(obj_location:str, **params):
        if not os.path.exists(obj_location):
            return cls(obj_location, **params)
        else:
            with open(obj_location, "rb") as f:
                __dict =  pickle.load(f)
                
            new = cls(__dict["obj_location"])
            for k, v in __dict.items():
                setattr(new, k, v)
        
            return new

    return get_instance

@if_available_deserialize 
class BaseCluster:    
    def __init__(self, obj_location:str, **params):
        self.obj_location = obj_location
        self.__setup__(params)
    
    @staticmethod
    def __hash_text_sha256__(text):
        return hashlib.sha256(text.encode()).hexdigest()
    
    def __build_algorithm__(self):
        raise NotImplementedError("Subclass must implement abstract method")
            
    def __setup__(self, params):
        raise NotImplementedError("Subclass must implement abstract method")
        
    
    def update_db_index(self, _id, question, embed):
        raise NotImplementedError("Subclass must implement abstract method")
        
    def serialize(self) -> None:
        with open(self.obj_location, "wb") as f:
            pickle.dump(self.__dict__, f)
        
    
    def fit(self, force:bool=False):
        raise NotImplementedError("Subclass must implement abstract method")
        
    
    def predict_new_point(self, new_point, max_distance):
        """
        Predicts the cluster of a new point using Nearest Neighbors.
        If the closest cluster point is farther than `max_distance`, return -1 (noise).
        """
        raise NotImplementedError("Subclass must implement abstract method")
        
    def get_cluster_ids(self, embed:np.array, thresh_dist = 0.6):
        raise NotImplementedError("Subclass must implement abstract method")
    
    def get_cluster_centers(self):
        return self.cluster.cluster_centers_
    
    def get_cluster_info(self):
        return self.cluster.components_
        

