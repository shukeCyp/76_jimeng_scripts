class Exception(Exception):
    """基础异常类"""
    
    def __init__(self, code: str = "UNKNOWN_ERROR", message: str = "未知错误"):
        """初始化异常"""
        super().__init__(message)
        self.code = code
        self.message = message
    
    def __str__(self):
        """字符串表示"""
        return f"[{self.code}] {self.message}"