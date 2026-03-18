import sqlite3

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
    model TEXT,
    role TEXT,
    created_at REAL,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);
"""

CREATE_PARTS_TABLE = """
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,
    type TEXT,
    content TEXT,
    created_at REAL,
    FOREIGN KEY (message_id) REFERENCES messages (id)
);
"""

class Database:
    """数据库管理，负责数据的存储和查询"""

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(CREATE_SESSIONS_TABLE)
        self.cursor.execute(CREATE_MESSAGES_TABLE)
        self.cursor.execute(CREATE_PARTS_TABLE)
        self.conn.commit()

    def save_session(self, session_info):
        """保存会话信息到数据库"""
        self.cursor.execute(
            "INSERT INTO sessions (id, parent_id, directory, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_info.id, session_info.parentID, session_info.directory, session_info.title, session_info.time['created'], session_info.time['updated'])
        )
        self.conn.commit()

    def save_message(self, message_info):
        """保存消息信息到数据库"""
        self.cursor.execute(
            "INSERT INTO messages (id, session_id, model, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (message_info.id, message_info.sessionID, message_info.model, message_info.role, message_info.created_at)
        )
        self.conn.commit()

    def save_part(self, part_info):
        """保存消息部分信息到数据库"""
        self.cursor.execute(
            "INSERT INTO parts (message_id, type, content, created_at) VALUES (?, ?, ?, ?)",
            (part_info.messageID, part_info.type, part_info.content, part_info.created_at)
        )
        self.conn.commit()

    def load_messages(self, sessionID):
        """根据会话ID加载消息信息"""
        self.cursor.execute(
            "SELECT id, model, role, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (sessionID,)
        )
        messages = self.cursor.fetchall()
        result = []
        for msg in messages:
            message_info = {
                'id': msg[0],
                'model': msg[1],
                'role': msg[2],
                'created_at': msg[3],
                'parts': []
            }
            self.cursor.execute(
                "SELECT type, content FROM parts WHERE message_id = ? ORDER BY created_at ASC",
                (msg[0],)
            )
            parts = self.cursor.fetchall()
            for part in parts:
                part_info = {
                    'type': part[0],
                    'content': part[1]
                }
                message_info['parts'].append(part_info)
            result.append(message_info)
        return result

global_db = Database("database/v_agent.db")
