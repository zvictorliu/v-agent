class SessionStatus:

    def __init__(self):
        self._state = {}

    def get(self, sessionID):
        """获取会话状态"""
        return self._state.get(sessionID)
    
    def set(self, sessionID, status):
        """设置会话状态"""
        self._state[sessionID] = status

global_session_status = SessionStatus()