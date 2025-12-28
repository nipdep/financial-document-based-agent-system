from pydantic import BaseModel
from typing import Optional

from cgcore.llm.base import BaseLlm
from cgcore.utils.prompt_template import fill_template

class Judge:
    def __init__(self, llm: BaseLlm, rule: BaseModel, prompt_template: Optional[str]=""):
        self.llm = llm
        self.rule = rule
        self.prompt_template = prompt_template

    def judge(self, prompt: str) -> bool:
        response = self.llm.structured_generate(prompt, self.rule)
        return response
    
    def judge_with_context(self, prompt: str, context: dict) -> bool:
        prompt = fill_template(self.prompt_template, prompt, context=context)
        response = self.llm.structured_generate(prompt, self.rule)
        return response