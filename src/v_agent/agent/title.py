from ..session.llm import LLM
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

SYSTEM_PROMPT = '''
Generate a concise, sentence-case title (3-7 words) that captures the main topic or goal of this coding session.
The title should be clear enough that the user recognizes the session in a list.
Use sentence case: capitalize only the first word and proper nouns.
'''

def isDefaultTitle(title):
    if 'New Session' in title:
        return True
    return False

def ensureTitle(session_info, input):
    '''
    
    '''
    msgs = [SystemMessage(SYSTEM_PROMPT), HumanMessage(input.content)]
    client = LLM(input.options)
    llm_input = LLM.StreamInput(msgs, session_info.id)
    if not isDefaultTitle(session_info.title):
        return
    try:
        session_info.title = client.invoke(llm_input).content
    except:
        logger.error('Query title failed.')
