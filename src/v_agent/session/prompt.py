from .status import SessionStatus, global_session_status
from .process import SessionProcess
from .system import SystemPrompt
from .llm import LLM
from .message import Message, toModelMessages
from ..storage.db import global_db

class SessionPrompt:

    def __init__(self):
        pass

    class PromptInput:
        def __init__(self, sessionID, messageID, model, agent, tools):
            self.sessionID = sessionID
            self.messageID = messageID
            self.model = model
            self.agent = agent
            self.tools = tools

    def loop(self, sessionID):
        """根据会话ID获取提示词并循环处理"""
        while True:
            # 设置为 busy 状态
            global_session_status.set(sessionID, 'busy')

            # TODO: 还要检测 abort 信号

            # TODO: 从数据库中加载历史消息
            db_msgs = global_db.load_messages(sessionID)

            # TODO: 将 msgs 转换为 langchain 的消息格式，作为 LLM 的输入
            model_messages = toModelMessages(db_msgs, input.model)

            # TODO: 处理 tasks

            stream_input = LLM.StreamInput(
                messages=model_messages,
                sessionID=sessionID
            )

            processor = SessionProcess(sessionID)
            result = processor.process(stream_input)

            if result == 'stop':
                break

    def createUserMessage(self, input: PromptInput) -> Message:
        """根据输入创建用户消息"""
        id = input.messageID # if messageID is None, generate a new one
        info = Message.Info(id=id, model=input.model)

        # TODO: 把 input.parts 转换成 Message.Part 的格式
        # 两种特殊的：file 和 agent

        # 存入数据库， loop 从数据库里面读取全部历史消息，不是显示发送这条
        global_db.save_message(info)

    def prompt(self, input: PromptInput):
        '''
        从数据库中获取session
        根据输入生成message
        '''

        # 生成用户消息
        _ = self.createUserMessage(input)

        # 启动
        self.loop(input.sessionID)