from loguru import logger
import time
from ..storage.db import global_db
from ..utils.id import Identifier

class Session:
    """会话管理，包含上下文管理、消息格式转换等功能"""
    def __init__(self):
        pass

    class Info:
        """会话信息，包含会话ID、上下文等"""
        def __init__(self):
            pass

    def createNext(self, input):
        """创建一个新的会话具体实现 主要需要考虑数据库"""
        result = Session.Info()
        result.id = Identifier.generateID('session_')
        result.directory = input.directory
        result.title = input.title if input.title else "New Session" + time.strftime(" %Y-%m-%d %H:%M:%S", time.localtime())
        result.time = {
            'created': time.time(),
            'updated': time.time()
        }

        logger.info('Created new session with ID: {id}', id=result.id)

        # TODO:保存到数据库
        global_db.save_session(result)

        return result

    def create(self, input):
        """创建一个新的会话"""
        return self.createNext(
            {
                'parentID': input.parentID,
                'directory': input.directory,
                'title': input.title
            }
        )

