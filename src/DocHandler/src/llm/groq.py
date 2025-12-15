from langchain_groq import ChatGroq  # Import ChatGroq from langchain_groq

from chatgenie.llm.base import BaseLlm

from icecream import ic


class GroqLlm(BaseLlm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_client()

    def _create_client(self):
        kwargs = {
            "groq_api_key": self.config.api_key,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "model_kwargs": {},
        }
        if self.config.top_p:
            kwargs["model_kwargs"]["top_p"] = self.config.top_p
        if self.config.stream: # XXX: haven't tested
            from langchain.callbacks.streaming_stdout import \
                StreamingStdOutCallbackHandler

            self.llm = ChatGroq(**kwargs, streaming=self.config.stream,
                              callbacks=[StreamingStdOutCallbackHandler()])
        else:
            self.llm = ChatGroq(**kwargs)