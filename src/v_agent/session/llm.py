from ..provider.provider import ProviderOptions
from langchain_qwq import ChatQwen
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage


class LLM:
    """大模型接入"""

    def __init__(self, options: ProviderOptions, tools=None):
        self.options = options

        if options.provider == "alibaba":
            self._client = ChatQwen(
                model=options.model,
                api_key=options.api_key,
                base_url=options.base_url,
            )
        elif options.provider == "openai":
            self._client = ChatOpenAI(
                model=options.model,
                api_key=options.api_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {options.provider}")

        if tools:
            self._client = self._client.bind_tools(tools) # 注意这里是返回新对象

    class StreamInput:
        """流式输入格式"""

        def __init__(self, messages: list[BaseMessage], sessionID):
            self.messages = messages  # 转换为 langchain 的消息格式
            self.sessionID = sessionID  # 这些都是后话了

    async def invoke(self, input):
        """非流式输出，适合标题总结"""
        return await self._client.ainvoke(input.messages)

    async def stream(self, input):  # 这里需定义自己的输入格式，其中包含 langchain 的消息格式
        """流式处理用户问题"""
        async for chunk in self._client.astream(input.messages):
            yield chunk
