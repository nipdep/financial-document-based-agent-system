from typing import Optional
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

class BaseLlm:
    def __init__(self, config):
        self.config = config
    
    def _create_client(self):
        raise NotImplementedError

    def generate(self, prompt, system_prompt="") -> str:
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        return self.llm.invoke(messages).content

    def structured_generate(self, prompt: str, structure: BaseModel, system_prompt: Optional[str] = "") -> dict:
        structured_llm = self.llm.with_structured_output(structure)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = structured_llm.invoke(messages)
        return response
