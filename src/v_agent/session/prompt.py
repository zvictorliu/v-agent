from .status import SessionStatus, global_session_status
from .process import SessionProcessor
from .system import SystemPrompt
from .llm import LLM
from . import message as MessageModule
from ..storage.db import global_db
from ..utils import id as Identifier
from ..provider.provider import ProviderOptions
from dataclasses import dataclass
import time


@dataclass
class PromptInput:
    sessionID: str
    options: ProviderOptions
    content: str


def loop(input: PromptInput):
    """根据会话ID获取提示词并循环处理"""
    while True:
        # 设置为 busy 状态
        global_session_status.set(input.sessionID, "busy")

        # TODO: 还要检测 abort 信号

        # TODO: 从数据库中加载历史消息
        db_msgs = global_db.load_messages(input.sessionID)

        # TODO: 将 msgs 转换为 langchain 的消息格式，作为 LLM 的输入
        model_messages = MessageModule.toModelMessages(db_msgs)

        # TODO: 处理 tasks

        stream_input = LLM.StreamInput(
            messages=model_messages, sessionID=input.sessionID
        )

        processor = SessionProcessor(input.sessionID, input.options)
        result = processor.process(stream_input)

        if result == "stop":
            break


def createUserMessage(input: PromptInput) -> MessageModule.Message:
    """根据输入创建用户消息"""
    msg_id = Identifier.generateID("msg_")
    info = {
        "id": msg_id,
        "sessionID": input.sessionID,
        "role": "user",
        "time": time.time(),
        "summary": "",
        "agent": "",
        "model": "",
    }
    part_id = Identifier.generateID("part_")
    parts = [
        {
            "id": part_id,
            "sessionID": input.sessionID,
            "messageID": msg_id,
            "type": "text",
            "text": input.content,
        }
    ]

    # TODO: 把 input.parts 转换成 Message.Part 的格式
    msg_info = MessageModule.MessageInfo(**info)
    msg_parts = [MessageModule.MessagePart(**part) for part in parts]
    msg = MessageModule.Message(msg_info, msg_parts)

    # 两种特殊的：file 和 agent

    # 存入数据库， loop 从数据库里面读取全部历史消息，不是显示发送这条
    global_db.save_message(msg.info)
    for part in msg.parts:
        global_db.save_part(part)

    return msg


def prompt(input: PromptInput):
    """
    从数据库中获取session
    根据输入生成message
    """

    # 生成用户消息
    _ = createUserMessage(input)

    # 启动
    loop(input)
