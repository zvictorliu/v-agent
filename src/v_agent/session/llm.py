from ..provider.provider import ProviderOptions
from langchain_qwq import ChatQwen
from langchain_openai import ChatOpenAI

class LLM:
    """大模型接入"""
    def __init__(self, options: ProviderOptions):
        self.options = options

        if options.provider == "alibaba":
            self._client = ChatQwen(
                model=options.model,
                api_key=options.api_key,
                base_url="https://api.dashscope.com/v1",
            )
        elif options.provider == "openai":
            self._client = ChatOpenAI(
                model=options.model,
                api_key=options.api_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {options.provider}")