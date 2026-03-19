from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dataclasses import dataclass

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
    '''消息类'''
    def __init__(self, info, parts):
        self.info = info
        self.parts = parts


def toModelMessages(msgs):
    '''转换成模型输入的消息格式'''
    model_messages = []
    for message in msgs:
        if message.info.role == 'user':
            model_messages.append(HumanMessage(content=message.parts[0].text))
        elif message.info.role == 'assistant':
            text = [part.text for part in message.parts if part.type == "text"]
            model_messages.append(AIMessage(content=text[0] if text else ""))
        elif message.info.role == 'system':
            model_messages.append(SystemMessage(content=message.parts[0].text))
        else:
            raise ValueError(f"Unknown message role: {message.info.role}")
    return model_messages