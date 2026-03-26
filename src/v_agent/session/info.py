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

@dataclass
class ProjectInfo:
    '''项目信息'''
    id: str
    name: str
    worktree: str

@dataclass
class GlobalInfo(SessionInfo):
    '''全局信息'''
    '''扩展 SessionInfo 的全局信息，包括项目信息'''
    project: ProjectInfo

