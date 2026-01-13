from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
import asyncio
class BaseLlm:
    def __init__(self, config):
        self.config = config
    
    def _create_client(self):
        raise NotImplementedError

    async def generate(self, prompt, system_prompt="") -> str:
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        response = await asyncio.to_thread(self.llm.invoke, messages)
        return response.content

    async def structured_generate(self, prompt: str, structure: BaseModel, system_prompt: Optional[str] = "") -> dict:
        structured_llm = self.llm.with_structured_output(structure)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = structured_llm.invoke(messages)
        return response
