import os
import sys
import yaml
import logging
from typing import Any, Dict, Optional
import socket

# Add the configs directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..environment import environment
from ..util import get_ip_addresses_by_ipv4

CONFIG_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'configs', environment.env, "service.yml")

class ServiceConfig:
    """服务配置类"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """初始化服务配置"""
        if options is None:
            options = {}
            
        self.name = options.get("name", "jimeng-free-api")
        self.host = options.get("host", "0.0.0.0")
        self.port = options.get("port", 5100)
        self.urlPrefix = options.get("urlPrefix", "")
        self.bindAddress = options.get("bindAddress", None)
    
    @property
    def addressHost(self) -> str:
        """获取地址主机"""
        if self.bindAddress:
            return self.bindAddress
            
        ip_addresses = get_ip_addresses_by_ipv4()
        for ip_address in ip_addresses:
            if ip_address == self.host:
                return ip_address
                
        return ip_addresses[0] if ip_addresses else "127.0.0.1"
    
    @property
    def address(self) -> str:
        """获取地址"""
        return f"{self.addressHost}:{self.port}"
    
    @property
    def pageDirUrl(self) -> str:
        """获取页面目录URL"""
        return f"http://127.0.0.1:{self.port}/page"
    
    @property
    def publicDirUrl(self) -> str:
        """获取公共目录URL"""
        return f"http://127.0.0.1:{self.port}/public"
    
    @staticmethod
    def load():
        """加载配置"""
        external = {k: v for k, v in environment.__dict__.items() 
                   if k in ["name", "host", "port"] and v is not None}
        
        if not os.path.exists(CONFIG_PATH):
            return ServiceConfig(external)
            
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return ServiceConfig({**data, **external})
        except Exception as e:
            logging.warning(f"Failed to load service config: {e}")
            return ServiceConfig(external)