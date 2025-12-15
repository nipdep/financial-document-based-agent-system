from icecream import ic 

class LLM:
    def __new__(self, llm_type, **kwargs):
        """Initialize a base LLM class

        :param config: LLM configuration option class, defaults to None
        :type config: Optional[BaseLlmConfig], optional
        """
        self.__create_concrete__(self, llm_type, **kwargs)
        return self._cls_concrete
        
    def __create_concrete__(self, llm_type, **kwargs):
        if llm_type == "openai":
            from chatgenie.llm.openai import OpenAILlm
            from chatgenie.config.llm.openai import OpenAILlmConfig
            config = OpenAILlmConfig(**kwargs)
            self._cls_concrete = OpenAILlm(config)
        elif llm_type == "groq":
            from chatgenie.llm.groq import GroqLlm
            from chatgenie.config.llm.groq import GroqLlmConfig
            config = GroqLlmConfig(**kwargs)
            self._cls_concrete = GroqLlm(config)
        else:
            raise NotImplementedError