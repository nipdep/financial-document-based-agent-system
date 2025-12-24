from langchain_classic.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from chatgenie.llm.base import BaseLlm
from chatgenie.utils.prompt_template import fill_template

from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache


class Generator:
    def __init__(self,
                 llm: BaseLlm,
                 prompt_template: str,
                 system_prompt: str = "",
                 memory_type: str = "none",
                 memory_size: int = 0,
                 use_cache: bool = False):
        self.llm = llm
        self.prompt_template = prompt_template
        self.system_prompt = system_prompt
        self.memory = self._select_memory(memory_type, memory_size)

        if use_cache:
            set_llm_cache(InMemoryCache())

    def _select_memory(self, memory, memory_size):
        if memory == "none":
            return None
        elif memory == "buffer":
            return ConversationBufferMemory()
        elif memory == "window_buffer":
            return ConversationBufferWindowMemory(k=memory_size)
        else:
            raise ValueError(f"Invalid memory type: {memory}")

    def generate(self, input_query):
        if self.memory:
            memory = self.memory.load_memory_variables({})['history']
            prompt = fill_template(self.prompt_template, input_query, history=memory)
        else:
            prompt = fill_template(self.prompt_template, input_query)
        response = self.llm.generate(prompt, self.system_prompt)
        if self.memory:
            self.memory.save_context({"input_query": input_query}, {"output": response})
        return response

    def generate_with_context(self, input_query, context):
        if self.memory:
            memory = self.memory.load_memory_variables({})['history']
            prompt = fill_template(self.prompt_template, input_query, history=memory, context=context)
        else:
            prompt = fill_template(self.prompt_template, input_query, context=context)
        response = self.llm.generate(prompt, self.system_prompt)
        if self.memory:
            self.memory.save_context({"input_query": input_query}, {"output": response})
        return response
