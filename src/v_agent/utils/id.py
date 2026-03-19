import uuid
   
def generateID(prefix=''):
    '''生成唯一 ID'''
    return prefix + str(uuid.uuid4())