
from enum import Enum
from typing import List, Dict, Union
import os
import hashlib
import numpy as np
import pickle
from cgcore.vectordb.base import BaseVectorDB
from QuestionAnswering.src.resources.transformations.clustering.base_cluster import MemoryUnit, ClusterTypes, if_available_deserialize

try:
    from sklearn.cluster import OPTICS, DBSCAN
    from sklearn.neighbors import NearestNeighbors
except ImportError:
    print("ImportError: sklearn not installed , Please install scikit-learn")

    
class ClusterTypes(Enum):
    OPTICS = "OPTICS"
    DBSCAN = "DBSCAN"
    SOM = "SOM"

@if_available_deserialize 
class DensityBasedCluster:    
    def __init__(self, obj_location:str, type:ClusterTypes = ClusterTypes.DBSCAN, **params):
        self.type = type
        super().__init__(obj_location, **params)
    
    def __build_algorithm__(self):
        if self.type == ClusterTypes.OPTICS:
            self.cluster = OPTICS()
        elif self.type == ClusterTypes.DBSCAN:  
            self.cluster = DBSCAN()
        else:
            raise NotImplementedError("Cluster type not implemented")
        
            
    def __setup__(self, params):
        self.q_map = {}
        self.embeddings = []
        self.embed_map = {}
        self._ids_map = {}
        self.cluster_ids = None
        self.cache_valid = False
        
        if "n_jobs" not in params:
            params["n_jobs"] = -1
            
        self.__build_algorithm__()
        self.cluster.set_params(**params)
    
    def update_db_index(self, _id, question, embed):
        unq_id = str(_id)+question
        unq_id = self.__hash_text_sha256__(unq_id)
        
        self.q_map[unq_id] = question
        self._ids_map[unq_id] = _id
        self.embed_map[len(self.embeddings)] = unq_id
        self.embeddings.append(embed)
        self.cache_valid = False
        return unq_id
        
    def serialize(self) -> None:
        with open(self.obj_location, "wb") as f:
            pickle.dump(self.__dict__, f)
        
    
    def fit(self, force:bool=False):
        if self.cache_valid and not force:
            return
        data = np.array(self.embeddings)
        self.cluster.fit(data)
        self.clustered_points = data[self.cluster.labels_ != -1]
        self.clustered_labels = self.cluster.labels_[self.cluster.labels_ != -1]
        
        # Fit Nearest Neighbors on clustered points
        self.nn = NearestNeighbors(n_neighbors=1).fit(self.clustered_points)
        self.cache_valid = True
        
    
    def predict_new_point(self, new_point, max_distance):
        """
        Predicts the cluster of a new point using Nearest Neighbors.
        If the closest cluster point is farther than `max_distance`, return -1 (noise).
        """
        distance, index = self.nn.kneighbors([new_point])  # Find nearest clustered point
        if distance[0][0] > max_distance:  # Check if too far from any cluster
            return -1  # Mark as noise
        return self.clustered_labels[index[0][0]]
        
    def get_cluster_ids(self, embed:np.array, thresh_dist = 0.6):
        if not self.cache_valid:
            self.fit()
        pred = self.predict_new_point(embed, thresh_dist)
        
        if pred == -1:
            return []
        
        sel_points = np.where(self.cluster.labels_ == pred)[0]
        sel_unq_id = [self.embed_map[i] for i in sel_points]
        sel_chunk_id = [self._ids_map[i] for i in sel_unq_id]
        unq_id, unq_count = np.unique(sel_chunk_id, return_counts=True) 
        info = [{"chunk_id":i1, "count":i2} for i1,i2 in zip(unq_id, unq_count)]
        
        return info
    
    def get_cluster_centers(self):
        return self.cluster.cluster_centers_
    
    def get_cluster_info(self):
        return self.cluster.components_
        