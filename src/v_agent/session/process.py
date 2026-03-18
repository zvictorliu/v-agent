from .llm import LLM

class SessionProcess:
    def __init__(self, sessionID):
        self.sessionID = sessionID

    def process(self, input : LLM.StreamInput):
        """处理会话"""
        while True:
            for chunk in LLM.stream(input):
                yield chunk