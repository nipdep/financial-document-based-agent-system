from typing import Optional
from chatgenie.config.llm.base import BaseLlmConfig
from chatgenie.helper.json_serializable import register_deserializable

@register_deserializable
class GroqLlmConfig(BaseLlmConfig):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = "llama-3.3-70b-versatile",
        temperature: Optional[float] = 0,
        max_tokens: Optional[int] = 1000,
        top_p: Optional[float] = 1
    ):
        # self.api_key = api_key 
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, top_p=top_p, api_key=api_key)
