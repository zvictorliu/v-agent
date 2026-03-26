from loguru import logger
import time
from ..storage.db import global_db
from ..utils import id as Identifier
from .info import SessionInfo, GlobalInfo


# ---------------------------
# session 生命周期管理
# ---------------------------
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


def get(id):
    """获取会话信息"""
    # 从数据库获取会话信息
    return global_db.get_session(id)


def fork(sessionID, messageID):
    """基于现有会话创建一个新分支，克隆直到指定消息为止的所有消息和内容块"""
    # 获取原会话信息
    original_session = get(sessionID)
    if original_session is None:
        logger.error("Original session with ID {id} not found", id=sessionID)
        return None

    # 创建新会话 (修改标题)
    title = original_session.title + " (Forked)"
    new_session = createNext(
        {
            "parentID": original_session.id,
            "directory": original_session.directory,
            "title": title,
        }
    )
    logger.info(
        "Forked new session with ID: {id} from original session ID: {original_id}",
        id=new_session.id,
        original_id=sessionID,
    )

    # 获取原会话消息历史，另存
    msgs = global_db.load_messages(sessionID)
    for msg in msgs:
        # TODO: 理论上应该确保 id 是有序的
        if msg.info.id >= messageID:
            break
        msg.info.id = Identifier.generateID("msg_")  # 生成新的消息ID
        msg.info.sessionID = new_session.id
        global_db.save_message(msg.info)
        # 获取消息的内容块，另存
        for part in msg.parts:
            part.info.id = Identifier.generateID("part_")  # 生成新的内容块ID
            part.info.sessionID = new_session.id
            part.info.messageID = msg.info.id
            global_db.save_part(part.info)

    return new_session


def remove(id):
    """删除会话及其关联的所有数据"""
    global_db.remove_session(id)
    logger.info("Removed session with ID: {id} and all its messages and parts", id=id)


def touch(id):
    """更新会话的更新时间"""
    updated_at = time.time()
    global_db.update_session_time(id, updated_at)
    logger.info(
        "Touched session with ID: {id}, new updated_at: {updated_at}",
        id=id,
        updated_at=updated_at,
    )


# --------------------------
# 会话属性操作
# --------------------------


# --------------------------
# 列表与查询
# --------------------------
def list():
    """列出所有会话"""
    return global_db.list_sessions()


# ---------------------------
# 其它工具函数
# ---------------------------
def setTitle(sessionID, title):
    """修改指定 session 的 title"""
    global_db.update_session_title(sessionID, title)
    touch(sessionID)
    logger.info("Updated title for session {id} to: {title}", id=sessionID, title=title)
