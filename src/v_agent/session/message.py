from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from dataclasses import dataclass
import json


@dataclass
class MessageInfo:
    id: str
    sessionID: str
    role: str
    time: float
    summary: str
    agent: str
    model: str


@dataclass
class MessagePart:
    id: str
    sessionID: str
    messageID: str
    type: str
    text: str


class Message:
    """消息类"""

    def __init__(self, info, parts):
        self.info = info
        self.parts = parts


def toModelMessages(msgs):
    """转换成模型输入的消息格式"""
    model_messages = []
    for message in msgs:
        if message.info.role == "user":
            model_messages.append(HumanMessage(content=message.parts[0].text))
        elif message.info.role == "assistant":
            content = ""
            tool_calls = []
            for part in message.parts:
                if part.type == "text":
                    content = part.text
                elif part.type == "tool-calls":
                    try:
                        tool_calls = json.loads(part.text)
                    except json.JSONDecodeError:
                        pass
            model_messages.append(AIMessage(content=content, tool_calls=tool_calls))
        elif message.info.role == "tool":
            # 存储格式：{"id": "...", "result": "..."}
            try:
                data = json.loads(message.parts[0].text)
                model_messages.append(
                    ToolMessage(content=str(data["result"]), tool_call_id=data["id"])
                )
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
        elif message.info.role == "system":
            model_messages.append(SystemMessage(content=message.parts[0].text))
        else:
            raise ValueError(f"Unknown message role: {message.info.role}")
    return model_messages
