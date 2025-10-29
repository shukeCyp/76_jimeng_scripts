import time
from typing import Any

class FailureBody:
    """失败响应体"""
    
    def __init__(self, error: Exception, data: Any = None):
        """初始化失败响应体"""
        self.code = getattr(error, 'code', 'UNKNOWN_ERROR')
        self.message = str(error)
        self.data = data
        self.time = int(time.time())