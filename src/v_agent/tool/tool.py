from langchain.tools import tool
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

available_tools = {
    "get_weather": get_weather,
    "calculate": calculate,
    "search_web": search_web,
}