from loguru import logger
import time
from ..storage.db import global_db
from ..utils import id as Identifier
from .info import SessionInfo


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

    result = SessionInfo(
        id=id,
        parentID=parentID,
        directory=directory,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
    )

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

def fork(input):
    '''fork一个新的会话'''

def get(id):
    """获取会话信息"""
    # opencode 这里是返回了一个SessionInfo对象 但这个对象有什么用？
    pass


def list():
    """列出所有会话"""
    return global_db.list_sessions()
