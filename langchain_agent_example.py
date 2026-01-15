"""LangChain Agent 示例 - 基于 OpenAI 兼容 API"""

import os
from dotenv import load_dotenv
from langchain_qwq import ChatQwen
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

# 加载环境变量
load_dotenv()

# 定义工具函数
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    weather_data = {
        "北京": "北京天气: 晴，15°C",
        "上海": "上海天气: 多云，18°C",
        "杭州": "杭州天气: 雨，12°C",
    }
    return weather_data.get(city, f"未知城市: {city}")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def search_web(query: str) -> str:
    """网络搜索工具（模拟）"""
    results = {
        "python": "Python 是一门流行的编程语言，常用于 AI 和数据科学。",
        "langchain": "LangChain 是一个用于构建 LLM 应用的框架。",
    }
    for key, value in results.items():
        if key in query.lower():
            return value
    return f"搜索 '{query}' 的结果未找到。"


# 工具列表
tools = [get_weather, calculate, search_web]


def create_chat_model():
    """创建聊天模型 - 使用 ChatQwen"""
    return ChatQwen(
        model="qwen-max",
        api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("DASHSCOPE_API_BASE") or os.getenv("OPENAI_API_HOST"),
    )


class SimpleAgent:
    """简单的 Tool Calling Agent"""

    def __init__(self, llm, tools):
        self.llm = llm.bind_tools(tools)
        self.tools = {t.name: t for t in tools}

    def invoke(self, question):
        """处理用户问题"""
        messages = [HumanMessage(content=question)]

        # 第一次调用 LLM
        response = self.llm.invoke(messages)

        # 如果有工具调用，执行并继续对话
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = response.tool_calls
            messages.append(response)

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # 执行工具
                if tool_name in self.tools:
                    result = self.tools[tool_name].invoke(tool_args)
                    messages.append(
                        ToolMessage(content=result, tool_call_id=tool_call["id"])
                    )

            # 第二次调用 LLM 获取最终回复
            final_response = self.llm.invoke(messages)
            return final_response.content

        return response.content


def run_demo():
    """运行演示"""
    print("=" * 50)
    print("LangChain Agent 示例")
    print("=" * 50)
    print("支持的工具: get_weather, calculate, search_web")
    print("输入 'quit' 退出")
    print("=" * 50)

    # 创建模型和 agent
    llm = create_chat_model()
    agent = SimpleAgent(llm, tools)

    # 预设问题
    questions = [
        ("北京天气怎么样？", "天气查询"),
        ("计算 (10 + 5) * 2", "数学计算"),
        ("什么是 Python？", "知识搜索"),
        ("上海天气如何？", "天气查询"),
    ]

    for question, desc in questions:
        print(f"\n[{desc}] 用户: {question}")
        print("-" * 30)
        response = agent.invoke(question)
        print(f"Agent: {response}")


if __name__ == "__main__":
    run_demo()
