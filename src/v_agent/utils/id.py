import uuid
class Identifier:

    def generateID(self, prefix=''):
        '''生成唯一 ID'''
        return prefix + str(uuid.uuid4())