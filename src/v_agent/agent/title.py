from ..session.llm import LLM
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

MAX_TITLE_LEN = 48

SYSTEM_PROMPT = '''
Generate a concise title for following content.
Hard requirements:
- Output only the title text, no quotes, no punctuation suffix, no explanation.
- Keep it very short: 3-7 words, and no more than 48 characters.
- Use sentence case: capitalize only the first word and proper nouns.
- Focus on the core task/topic so it is easy to scan in a session list.
'''

def isDefaultTitle(title):
    if 'New Session' in title:
        return True
    return False


def _sanitize_title(text: str) -> str:
    title = (text or "").strip()
    if not title:
        return title
    # 去掉模型可能返回的包裹引号
    if (title.startswith('"') and title.endswith('"')) or (
        title.startswith("'") and title.endswith("'")
    ):
        title = title[1:-1].strip()
    # 去掉换行，压成单行标题
    title = " ".join(title.split())
    # 最终长度保护：过长时截断
    if len(title) > MAX_TITLE_LEN:
        title = title[: MAX_TITLE_LEN - 3].rstrip() + "..."
    return title

async def ensureTitle(session_info, input):
    '''
    
    '''
    msgs = [SystemMessage(SYSTEM_PROMPT), HumanMessage(input.content)]
    client = LLM(input.options, disable_thinking=True)
    llm_input = LLM.StreamInput(msgs, session_info.id)
    if not isDefaultTitle(session_info.title):
        return
    try:
        response = await client.invoke(llm_input)
        title = _sanitize_title(response.content)
        if title:
            session_info.title = title
    except Exception:
        logger.exception('Query title failed.')
