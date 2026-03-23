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
