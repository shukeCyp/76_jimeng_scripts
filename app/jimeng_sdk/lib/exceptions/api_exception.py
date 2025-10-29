from .exception import Exception

class APIException(Exception):
    """API异常类"""
    
    def __init__(self, code: str, message: str = ""):
        """初始化API异常"""
        super().__init__(code, message)