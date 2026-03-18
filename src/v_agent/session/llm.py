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
                base_url=options.base_url,
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
        def __init__(self, messages : list[BaseMessage], sessionID):
            self.messages = messages # 转换为 langchain 的消息格式
            self.sessionID = sessionID # 这些都是后话了
        
    def invoke(self, input):
        '''需要把自己定义的消息格式转换成大模型需要的格式'''
        pass

    def stream(self, input): # 这里需定义自己的输入格式，其中包含 langchain 的消息格式
        """流式处理用户问题"""
        for chunk in self._client.stream(input.messages):
            # 1. 优先提取推理内容 (Reasoning)
            # 注意：有些模型推理和正文会出现在同一个 chunk，有些是分开的
            reasoning = chunk.additional_kwargs.get("reasoning_content")
            if reasoning:
                yield {"type": "reasoning", "content": reasoning}
                # 如果该 chunk 只有推理，就跳过后续判断
                if not chunk.content: 
                    continue

            # 2. 提取工具调用信息 (Tool Calling)
            if chunk.tool_call_chunks:
                for tc in chunk.tool_call_chunks:
                    yield {
                        "type": "tool_calling",
                        "name": tc.get("name"),   # 仅在开始时有值
                        "args": tc.get("args"),   # 增量字符串
                        "id": tc.get("id")
                    }
                continue # 工具调用时通常没有 content

            # 3. 提取普通消息正文 (Message)
            if chunk.content:
                yield {"type": "message", "content": chunk.content}