import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Any

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Logger:
    """日志记录器"""
    
    def __init__(self):
        """初始化日志记录器"""
        self.logger = logging.getLogger("jimeng")
        self.logger.setLevel(logging.INFO)
    
    def header(self):
        """打印头部信息"""
        print("\033[1;32m" + "="*60 + "\033[0m")
        print("\033[1;32m" + "  Jimeng Free API - Python Version".center(60) + "\033[0m")
        print("\033[1;32m" + "="*60 + "\033[0m")
    
    def info(self, message: Any, *args):
        """记录INFO级别日志"""
        self.logger.info(str(message), *args)
    
    def success(self, message: Any, *args):
        """记录SUCCESS级别日志"""
        self.logger.info("\033[1;32m" + str(message) + "\033[0m", *args)
    
    def warn(self, message: Any, *args):
        """记录WARN级别日志"""
        self.logger.warning("\033[1;33m" + str(message) + "\033[0m", *args)
    
    def error(self, message: Any, *args):
        """记录ERROR级别日志"""
        self.logger.error("\033[1;31m" + str(message) + "\033[0m", *args)
    
    def debug(self, message: Any, *args):
        """记录DEBUG级别日志"""
        self.logger.debug("\033[1;36m" + str(message) + "\033[0m", *args)

# 全局日志实例
logger = Logger()