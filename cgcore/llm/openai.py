from chatgenie.llm.base import BaseLlm
from icecream import ic

try:
    from langchain_openai import ChatOpenAI
except ModuleNotFoundError:
    raise ModuleNotFoundError("Please install langchain_openai")

class OpenAILlm(BaseLlm):
    def __init__(self, config):
        super().__init__(config)
        self._create_client()

    def _create_client(self):
        kwargs = {
            "openai_api_key": self.config.api_key,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "model_kwargs": {},
        }
        if self.config.top_p: # XXX: need to update
            kwargs["model_kwargs"]["top_p"] = self.config.top_p

        if self.config.stream: # XXX: haven't tested
            from langchain.callbacks.streaming_stdout import \
                StreamingStdOutCallbackHandler

            self.llm = ChatOpenAI(**kwargs, streaming=self.config.stream,
                              callbacks=[StreamingStdOutCallbackHandler()])
        else:
            self.llm = ChatOpenAI(**kwargs)

    def clone(self, **updated_configs):
        """
        Creates a new instance of OpenAILlm with the same configuration,
        allowing updates to specific model configurations.
        
        :param updated_configs: Key-value pairs of config attributes to update
        :return: A new OpenAILlm instance with modified configurations
        """
        # Clone current config while applying updates
        new_config = self.config.copy()  # Assuming config supports copy()
        for key, value in updated_configs.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)

        kwargs = {
            "openai_api_key": self.config.api_key,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "model_kwargs": {},
        }
        if self.config.top_p: # XXX: need to update
            kwargs["model_kwargs"]["top_p"] = self.config.top_p

        if self.config.stream: # XXX: haven't tested
            from langchain.callbacks.streaming_stdout import \
                StreamingStdOutCallbackHandler

            self.llm = ChatOpenAI(**kwargs, streaming=self.config.stream,
                              callbacks=[StreamingStdOutCallbackHandler()])
        else:
            self.llm = ChatOpenAI(**kwargs)

    