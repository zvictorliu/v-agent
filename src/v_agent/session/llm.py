from ..provider.provider import ProviderOptions
from langchain_qwq import ChatQwen
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

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
        
    class StreamInput:
        """流式输入格式"""
        def __init__(self, messages : list[BaseMessage],
                    tools, agent, system : list[BaseMessage], sessionID):
            self.messages = messages # 转换为 langchain 的消息格式
            self.system = system # 系统提示词
            self.sessionID = sessionID # 这些都是后话了
        
    def invoke(self, input):
        '''需要把自己定义的消息格式转换成大模型需要的格式'''
        pass

    def stream(self, input): # 这里需定义自己的输入格式，其中包含 langchain 的消息格式
        """流式处理用户问题"""
        for chunk in self._client.stream(input.messages):
            yield chunk