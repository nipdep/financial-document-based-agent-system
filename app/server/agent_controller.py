from abc import ABC, abstractmethod

class AgentGeneration(ABC):
    def __init__(self) -> None:
        pass
    
    @abstractmethod
    async def request(self, request:str, agent_id:int=None) -> dict[str,str]:
        pass