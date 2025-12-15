
from typing import Optional
from chatgenie.config.llm.base import BaseLlmConfig
from chatgenie.helper.json_serializable import register_deserializable

@register_deserializable
class OpenAILlmConfig(BaseLlmConfig):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = 'gpt-3.5-turbo',
        temperature: Optional[float] = 0,
        max_tokens: Optional[int] = 500,
        top_p: Optional[float] = 1
    ):
        # self.api_key = api_key 
        super().__init__(model=model, temperature=temperature, max_tokens=max_tokens, top_p=top_p, api_key=api_key)
