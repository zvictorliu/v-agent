from .llm import LLM
from colorama import Fore
from . import message as MessageModule
from ..storage.db import global_db
from ..utils import id as Identifier
import time

class SessionProcessor:
    def __init__(self, sessionID, options):
        self.sessionID = sessionID
        self.client = LLM(options)

    def _save_current_part(self, current_type, full_content, message_id=""):
        if full_content:
            part_id = Identifier.generateID("part_")
            part_info = {
                "id": part_id,
                "sessionID": self.sessionID,
                "messageID": message_id,
                "type": "text" if current_type == "message" else "reasoning",
                "text": full_content,
            }
            part = MessageModule.MessagePart(**part_info)
            global_db.save_part(part)

    def process(self, input: LLM.StreamInput):
        """处理会话"""

        current_type = None
        response_stream = self.client.stream(input)
        full_content = ""
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
        for value in response_stream:
            new_type = value["type"]
            if new_type != current_type:
                if current_type is not None:
                    print()  # 切换类型时换行
                    self._save_current_part(current_type, full_content, message_id=msg_info.id)
                    full_content = ""  # 重置内容
                if new_type == "reasoning":
                    print(Fore.YELLOW + "[Reasoning] " + Fore.RESET, end="", flush=True)
                elif new_type == "message":
                    print(Fore.GREEN + "[Message] " + Fore.RESET, end="", flush=True)
                elif new_type == "tool_calling":
                    print(
                        Fore.BLUE + "[Tool Calling] " + Fore.RESET, end="", flush=True
                    )
                current_type = new_type

            if new_type == "reasoning":
                print(Fore.YELLOW + value["content"] + Fore.RESET, end="", flush=True)
                full_content += value["content"]
            elif new_type == "message":
                print(Fore.GREEN + value["content"] + Fore.RESET, end="", flush=True)
                full_content += value["content"]
            elif new_type == "tool_calling":
                print(
                    Fore.BLUE
                    + f"Tool: {value['name']}, Args: {value['args']}"
                    + Fore.RESET,
                    end="",
                    flush=True,
                )
        self._save_current_part(current_type, full_content, message_id=msg_info.id)
        full_content = ""  # 重置内容
        print()  # 结束时换行
        global_db.save_message(msg_info)
        return "stop"
