import os
import sys
import json

class Environment:
    """环境配置类"""
    
    def __init__(self):
        """初始化环境配置"""
        self.env = os.getenv("ENV", "dev")
        self.package = {
            "version": os.getenv("VERSION", "1.3.0")
        }
        self.name = os.getenv("SERVICE_NAME")
        port_str = os.getenv("PORT")
        self.port = int(port_str) if port_str and port_str.isdigit() else None

# 全局环境实例
environment = Environment()