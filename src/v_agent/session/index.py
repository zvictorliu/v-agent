from loguru import logger
import time
from ..storage.db import global_db
from ..utils import id as Identifier
from dataclasses import dataclass

@dataclass    
class SessionInfo:
    """Session 信息"""
    id: str
    parentID: str
    directory: str
    title: str
    created_at: float
    updated_at: float


def createNext(input):
    """创建一个新的会话具体实现 主要需要考虑数据库"""
    id = Identifier.generateID("session_")
    parentID = input.get("parentID", "")
    directory = input.get("directory", "")
    title = input.get("title", "") or "New Session" + time.strftime(
        " %Y-%m-%d %H:%M:%S", time.localtime()
    )
    created_at = time.time()
    updated_at = created_at

    result = SessionInfo(id=id, parentID=parentID, directory=directory, title=title, created_at=created_at, updated_at=updated_at)

    logger.info("Created new session with ID: {id}", id=result.id)

    # TODO:保存到数据库
    global_db.save_session(result)

    return result

def create(input):
    """创建一个新的会话"""
    return createNext(
        {
            "parentID": input.get("parentID"),
            "directory": input.get("directory"),
            "title": input.get("title"),
        }
    )
