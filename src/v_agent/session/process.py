import json
from .llm import LLM
from colorama import Fore
from . import message as MessageModule
from ..storage.db import global_db
from ..utils import id as Identifier
import time


class SessionProcessor:
    def __init__(self, sessionID, options, tools):
        self.sessionID = sessionID
        self.client = LLM(options, tools=tools)
        self.tools = {t.name: t for t in tools}

    def _save_current_part(self, part_type, content, message_id=""):
        """保存消息部分到数据库"""
        if content:
            part_id = Identifier.generateID("part_")
            part_info = {
                "id": part_id,
                "sessionID": self.sessionID,
                "messageID": message_id,
                "type": part_type,
                "text": str(content),
            }
            part = MessageModule.MessagePart(**part_info)
            global_db.save_part(part)

    def process(self, input: LLM.StreamInput):
        """处理一次会话"""
        full_response = None
        response_stream = self.client.stream(input)

        # 预先生成消息 ID，但先不保存，看最后是否有内容
        msg_id = Identifier.generateID("msg_")
        msg_info = {
            "id": msg_id,
            "sessionID": self.sessionID,
            "role": "assistant",
            "time": time.time(),
            "summary": "",
            "agent": "",
            "model": "",
        }
        msg_info = MessageModule.MessageInfo(**msg_info)

        message_saved = False

        for chunk in response_stream:
            # 打印流式文本（如果有的话）
            if chunk.content:
                print(chunk.content, end="", flush=True)
            # 累加 chunk 以获得完整的 tool_calls
            if full_response is None:
                full_response = chunk
            else:
                full_response += chunk  # AIMessageChunk 支持相加合并

        # 结果保存
        if full_response is not None:
            # 保存文本内容
            if hasattr(full_response, "content") and full_response.content:
                if not message_saved:
                    global_db.save_message(msg_info)
                    message_saved = True
                self._save_current_part(
                    "text", full_response.content, message_id=msg_id
                )

            # 保存工具调用
            if hasattr(full_response, "tool_calls") and full_response.tool_calls:
                if not message_saved:
                    global_db.save_message(msg_info)
                    message_saved = True
                self._save_current_part(
                    "tool-calls",
                    json.dumps(full_response.tool_calls),
                    message_id=msg_id,
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

                # 创建一个新的消息用于保存工具结果
                # 因为 langchain 的原因必须单独封装 ToolMessage 才能识别
                # 这点无法和 opencode 保持一致
                tool_msg_id = Identifier.generateID("msg_")
                tool_msg_info = MessageModule.MessageInfo(
                    id=tool_msg_id,
                    sessionID=self.sessionID,
                    role="tool",
                    time=time.time(),
                    summary="",
                    agent="",
                    model="",
                )
                global_db.save_message(tool_msg_info)

                # 存储格式：{"id": "...", "result": "..."}
                tool_result_data = json.dumps({"id": tool_id, "result": result})
                self._save_current_part(
                    "tool-result", tool_result_data, message_id=tool_msg_id
                )
            else:
                print(f"{Fore.RED}不支持的工具: {tool_name}{Fore.RESET}")
                return "stop"

        return "continue"
