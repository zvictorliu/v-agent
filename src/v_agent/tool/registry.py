from .tool import available_tools

class ToolRegistry:
    """工具注册中心，负责管理所有工具的注册和调用"""
    def __init__(self, tools):
        self._tools = [available_tools[t] for t in tools if t in available_tools]

    def get_tools(self):
        return self._tools