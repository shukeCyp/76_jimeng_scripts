import os
import sys

# Add the configs directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'configs'))

from .configs.service_config import ServiceConfig
from .configs.system_config import SystemConfig

class Config:
    """配置类"""
    
    def __init__(self):
        """初始化配置"""
        self.service = ServiceConfig.load()
        self.system = SystemConfig.load()

# 全局配置实例
config = Config()