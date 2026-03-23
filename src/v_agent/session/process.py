from .llm import LLM
from colorama import Fore
from . import message as MessageModule
from ..storage.db import global_db
from ..utils import id as Identifier
import time
from langchain_core.messages import ToolMessage


class SessionProcessor:
    def __init__(self, sessionID, options, tools):
        self.sessionID = sessionID
        self.client = LLM(options, tools=tools)
        self.tools = {t.name: t for t in tools}

    def _save_current_part(self, current_type, full_content, message_id=""):
        if full_content:
            part_id = Identifier.generateID("part_")
            part_info = {
                "id": part_id,
                "sessionID": self.sessionID,
                "messageID": message_id,
                "type": "text" if current_type == "message" else "tool-result",
                "text": full_content,
            }
            part = MessageModule.MessagePart(**part_info)
            global_db.save_part(part)

    def process(self, input: LLM.StreamInput):
        """处理会话"""
        max_retries = 5
        for _ in range(max_retries):
            full_response = None
            response_stream = self.client.stream(input)
            msg_info = {
                "id": Identifier.generateID("msg_"),
                "sessionID": self.sessionID,
                "role": "assistant",
                "time": time.time(),
                "summary": "",
                "agent": "",
                "model": "",
            }
            msg_info = MessageModule.MessageInfo(**msg_info)
            global_db.save_message(msg_info)
            for chunk in response_stream:
                # 打印流式文本（如果有的话）
                if chunk.content:
                    print(chunk.content, end="", flush=True)
                # 累加 chunk 以获得完整的 tool_calls
                if full_response is None:
                    full_response = chunk
                else:
                    full_response += chunk  # AIMessageChunk 支持相加合并

            # 将助手的回复添加到消息历史中，这对于后续的工具调用至关重要
            if full_response is not None:
                input.messages.append(full_response)
                if hasattr(full_response, "content") and full_response.content:
                    self._save_current_part(
                        "message", full_response.content, message_id=msg_info.id
                    )

            # --- 检查是否需要调用工具 ---
            if (
                full_response is None
                or not hasattr(full_response, "tool_calls")
                or not full_response.tool_calls
            ):
                # 如果没有工具调用，说明任务完成
                print()  # 换行
                return "stop"

            # --- 手动解析并执行工具 ---
            for tool_call in full_response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                print(
                    f"\n{Fore.YELLOW}工具调用: {tool_name}\n参数: {tool_args}{Fore.RESET}"
                )

                if tool_name in self.tools:
                    result = self.tools[tool_name].invoke(tool_args)
                    print(f"{Fore.GREEN}工具结果: {result}{Fore.RESET}")

                    # 把工具结果作为新的消息部分保存，并继续对话
                    self._save_current_part(
                        "tool-result", result, message_id=msg_info.id
                    )

                    # 封装为 ToolMessage 继续对话
                    tool_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_id,
                    )
                    input.messages.append(tool_message)
                else:
                    print(f"{Fore.RED}不支持的工具: {tool_name}{Fore.RESET}")
                    return "stop"
            # 执行完成后，继续下一轮对话，直到没有工具调用为止
