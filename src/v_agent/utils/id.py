import time
import uuid


def generateID(prefix=""):
    """生成唯一有序 ID"""
    # 使用纳秒级时间戳确保有序性 (larger than before)
    # 并附加 uuid 的一部分以确保在极高并发下的唯一性
    timestamp = time.time_ns()
    random_part = uuid.uuid4().hex[:8]
    return f"{prefix}{timestamp}_{random_part}"
