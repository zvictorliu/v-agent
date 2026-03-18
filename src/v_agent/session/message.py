class Message:
    '''消息类'''

    class Info:
        '''消息的属性信息'''
        id : str
        model : str

    class Part:
        '''消息的内容 具体的消息'''
        def __init__(self, content):
            pass

    info : Info
    parts : list[Part]