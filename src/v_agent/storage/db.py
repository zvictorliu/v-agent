import sqlite3
from ..session import message as MessageModule
from ..session.info import SessionInfo

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    directory TEXT,
    title TEXT,
    created_at REAL,
    updated_at REAL
);
"""

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    role TEXT,
    time REAL,
    summary TEXT,
    agent TEXT,
    model TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);
"""

CREATE_PARTS_TABLE = """
CREATE TABLE IF NOT EXISTS parts (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    message_id TEXT,
    type TEXT,
    text TEXT,
    FOREIGN KEY (message_id) REFERENCES messages (id)
);
"""


class Database:
    """数据库管理，负责数据的存储和查询"""

    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute(CREATE_SESSIONS_TABLE)
        self.cursor.execute(CREATE_MESSAGES_TABLE)
        self.cursor.execute(CREATE_PARTS_TABLE)
        self.conn.commit()

    def save_session(self, session_info):
        """保存会话信息到数据库"""
        self.cursor.execute(
            "INSERT INTO sessions (id, parent_id, directory, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_info.id,
                session_info.parentID,
                session_info.directory,
                session_info.title,
                session_info.created_at,
                session_info.updated_at,
            ),
        )
        self.conn.commit()

    def save_message(self, message_info):
        """保存消息信息到数据库"""
        self.cursor.execute(
            "INSERT INTO messages (id, session_id, role, time, summary, agent, model) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                message_info.id,
                message_info.sessionID,
                message_info.role,
                message_info.time,
                message_info.summary,
                message_info.agent,
                message_info.model,
            ),
        )
        self.conn.commit()

    def save_part(self, part_info):
        """保存消息部分信息到数据库"""
        self.cursor.execute(
            "INSERT INTO parts (id, session_id, message_id, type, text) VALUES (?, ?, ?, ?, ?)",
            (
                part_info.id,
                part_info.sessionID,
                part_info.messageID,
                part_info.type,
                part_info.text,
            ),
        )
        self.conn.commit()

    def load_messages(self, sessionID):
        """根据会话ID加载消息信息"""
        self.cursor.execute(
            "SELECT id, model, role, time, summary, agent, model FROM messages WHERE session_id = ? ORDER BY time ASC",
            (sessionID,),
        )
        messages = self.cursor.fetchall()
        result = []
        for msg in messages:
            message_info = {
                "id": msg[0],
                "sessionID": sessionID,
                "role": msg[2],
                "time": msg[3],
                "summary": msg[4],
                "agent": msg[5],
                "model": msg[6],
            }
            msg_info = MessageModule.MessageInfo(**message_info)
            self.cursor.execute(
                "SELECT id, type, text FROM parts WHERE message_id = ? ORDER BY id ASC",
                (msg[0],),
            )
            parts = self.cursor.fetchall()
            msg_parts = []
            for part in parts:
                part_info = {
                    "id": part[0],
                    "sessionID": sessionID,
                    "messageID": msg[0],
                    "type": part[1],
                    "text": part[2],
                }
                part_info = MessageModule.MessagePart(**part_info)
                msg_parts.append(part_info)
            msg_ = MessageModule.Message(msg_info, msg_parts)
            result.append(msg_)
        return result

    def list_sessions(self):
        """列出所有会话"""
        self.cursor.execute(
            "SELECT id, parent_id, directory, title, created_at, updated_at FROM sessions ORDER BY created_at DESC"
        )
        sessions = self.cursor.fetchall()
        result = []
        for session in sessions:
            session_info = {
                "id": session[0],
                "parentID": session[1],
                "directory": session[2],
                "title": session[3],
                "created_at": session[4],
                "updated_at": session[5],
            }
            result.append(SessionInfo(**session_info))
        return result

    def get_session(self, id):
        """根据ID获取会话信息"""
        self.cursor.execute(
            "SELECT id, parent_id, directory, title, created_at, updated_at FROM sessions WHERE id = ?",
            (id,),
        )
        session = self.cursor.fetchone()
        if session:
            session_info = {
                "id": session[0],
                "parentID": session[1],
                "directory": session[2],
                "title": session[3],
                "created_at": session[4],
                "updated_at": session[5],
            }
            return SessionInfo(**session_info)
        else:
            return None

    def update_session_time(self, session_id, updated_at):
        """更新会话更新时间"""
        self.cursor.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (updated_at, session_id),
        )
        self.conn.commit()

    def remove_session(self, session_id):
        """从数据库中删除会话及其关联的所有数据"""
        self.cursor.execute("DELETE FROM parts WHERE session_id = ?", (session_id,))
        self.cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()

    def update_session_title(self, session_id, title):
        """更新会话标题"""
        self.cursor.execute(
            "UPDATE sessions SET title = ? WHERE id = ?",
            (title, session_id),
        )
        self.conn.commit()


global_db = Database("database/v_agent.db")
