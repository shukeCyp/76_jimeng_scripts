import os
import sys
import yaml
import logging
from typing import Any, Dict, Optional

# Add the configs directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..environment import environment

CONFIG_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'configs', environment.env, "system.yml")

class SystemConfig:
    """系统配置类"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """初始化系统配置"""
        if options is None:
            options = {}
            
        self.requestLog = options.get("requestLog", False)
        self.tmpDir = options.get("tmpDir", "./tmp")
        self.logDir = options.get("logDir", "./logs")
        self.logWriteInterval = options.get("logWriteInterval", 200)
        self.logFileExpires = options.get("logFileExpires", 2626560000)
        self.publicDir = options.get("publicDir", "./public")
        self.tmpFileExpires = options.get("tmpFileExpires", 86400000)
        self.requestBody = options.get("requestBody", {})
        
        # 合并默认的请求体配置
        default_request_body = {
            "enableTypes": ['form', 'text', 'xml'],  # 移除 json，由自定义中间件处理
            "encoding": 'utf-8',
            "formLimit": '100mb',
            "jsonLimit": '100mb',
            "textLimit": '100mb',
            "xmlLimit": '100mb',
            "formidable": {
                "maxFileSize": '100mb'
            },
            "multipart": True,
            "parsedMethods": ['POST', 'PUT', 'PATCH']
        }
        
        self.requestBody = {**default_request_body, **self.requestBody}
        
        self.debug = options.get("debug", True)
    
    @property
    def rootDirPath(self) -> str:
        """获取根目录路径"""
        return os.path.abspath(os.path.dirname(__file__) + "/../../..")
    
    @property
    def tmpDirPath(self) -> str:
        """获取临时目录路径"""
        return os.path.abspath(os.path.join(self.rootDirPath, self.tmpDir))
    
    @property
    def logDirPath(self) -> str:
        """获取日志目录路径"""
        return os.path.abspath(os.path.join(self.rootDirPath, self.logDir))
    
    @property
    def publicDirPath(self) -> str:
        """获取公共目录路径"""
        return os.path.abspath(os.path.join(self.rootDirPath, self.publicDir))
    
    @staticmethod
    def load():
        """加载配置"""
        if not os.path.exists(CONFIG_PATH):
            return SystemConfig()
            
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return SystemConfig(data)
        except Exception as e:
            logging.warning(f"Failed to load system config: {e}")
            return SystemConfig()