from langchain_core.tools import tool
import os
import subprocess
from typing import Optional

# 定义工具函数


@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息。

    Args:
        city (str): 城市名称，例如 "北京"、"上海"、"杭州"。

    Returns:
        str: 包含天气描述和温度的字符串，如果城市未知则返回错误信息。
    """
    weather_data = {
        "北京": "北京天气: 晴，15°C",
        "上海": "上海天气: 多云，18°C",
        "杭州": "杭州天气: 雨，12°C",
    }
    return weather_data.get(city, f"未知城市: {city}")


@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式。支持基本的算术运算。

    Args:
        expression (str): 要计算的数学表达式字符串，例如 "2 + 3 * 4"。

    Returns:
        str: 计算结果的字符串表示，如果发生错误则返回错误信息。
    """
    try:
        # 注意：在生产环境中使用 eval 存在安全风险，此处仅作为演示
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def search_web(query: str) -> str:
    """
    网络搜索工具（模拟），用于获取关于特定主题的信息。

    Args:
        query (str): 搜索查询字符串。

    Returns:
        str: 搜索结果摘要，如果未找到则返回相应提示。
    """
    results = {
        "python": "Python 是一门流行的编程语言，常用于 AI 和数据科学。",
        "langchain": "LangChain 是一个用于构建 LLM 应用的框架。",
    }
    for key, value in results.items():
        if key in query.lower():
            return value
    return f"搜索 '{query}' 的结果未找到。"


@tool
def read_file(file_path: str) -> str:
    """
    读取指定文件的文本内容。

    Args:
        file_path (str): 文件的路径（绝对路径或相对于工作目录的路径）。

    Returns:
        str: 文件的全文内容，或者包含详细原因的错误消息。
    """
    print(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"错误：找不到文件 '{file_path}'。"
    except PermissionError:
        return f"错误：没有权限访问文件 '{file_path}'。"
    except Exception as e:
        return f"发生未知错误: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    将内容写入指定路径的文件。如果文件已存在，将覆盖其内容。

    Args:
        file_path (str): 文件的路径（绝对路径或相对于工作目录的路径）。
        content (str): 要写入文件的字符串内容。

    Returns:
        str: 写入成功的确认消息，或者包含详细原因的错误消息。
    """
    print(file_path)
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return f"成功将内容写入文件 '{file_path}'。"
    except PermissionError:
        return f"错误：没有权限写入文件 '{file_path}'。"
    except Exception as e:
        return f"发生未知错误: {str(e)}"


@tool
def grep(file_path: str, pattern: str) -> str:
    """
    在指定文件中搜索包含特定模式的行。

    Args:
        file_path (str): 要搜索的文件路径。
        pattern (str): 要查找的文本字符串。

    Returns:
        str: 所有匹配行的组合字符串，如果未找到则返回相应提示，或返回错误消息。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            matching_lines = [line.strip() for line in file if pattern in line]
            if matching_lines:
                return "\n".join(matching_lines)
            else:
                return f"在文件 '{file_path}' 中未找到包含 '{pattern}' 的行。"
    except FileNotFoundError:
        return f"错误：找不到文件 '{file_path}'。"
    except PermissionError:
        return f"错误：没有权限访问文件 '{file_path}'。"
    except Exception as e:
        return f"发生未知错误: {str(e)}"


@tool
def execute_command(command: str) -> str:
    """
    在本地系统上执行 shell 命令并返回其输出。

    Args:
        command (str): 要执行的 shell 命令字符串。

    Returns:
        str: 命令的标准输出 (stdout)，如果有错误输出也会包含在内。
    """
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\n错误输出:\n{result.stderr}"
        return output if output else "命令执行成功，无输出。"
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时。"
    except Exception as e:
        return f"发生未知错误: {str(e)}"


available_tools = {
    "get_weather": get_weather,
    "calculate": calculate,
    "search_web": search_web,
    "read_file": read_file,
    "write_file": write_file,
    "grep": grep,
    "execute_command": execute_command,
}

# 引入我们刚才创建的 skill_tool，它会自动扫描技能并注入自身描述
try:
    from .skill import skill_tool

    available_tools["skill"] = skill_tool
except ImportError as e:
    print(f"Warning: Failed to load skill tool: {e}")
