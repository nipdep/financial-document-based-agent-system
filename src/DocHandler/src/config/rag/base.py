from typing import Optional

class BaseRAGConfig:
    def __init__(self,
                system_prompt: Optional[str] = "You are a helpful assistant.",
                history: Optional[bool] = False,
                memory_type: Optional[str] = "none",
                memory_size: Optional[int] = 0,
                ):
        self.system_prompt = system_prompt
        self.history = history
        self.memory_type = memory_type
        self.memory_size = memory_size


class GeneralRAGConfig(BaseRAGConfig):
    def __init__(self,
                system_prompt: Optional[str] = "You are a helpful assistant.",
                history: Optional[bool] = False,
                memory_type: Optional[str] = "none",
                memory_size: Optional[int] = 0,
                ):
        super().__init__(system_prompt=system_prompt, history=history, memory_type=memory_type, memory_size=memory_size)