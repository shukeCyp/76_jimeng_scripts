import os
import sys
import uuid
import hashlib
import socket
import base64
from typing import List

def get_ip_addresses_by_ipv4() -> List[str]:
    """获取IPv4地址列表"""
    ip_addresses = []
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        for ip in ip_list:
            if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                ip_addresses.append(ip)
    except Exception:
        pass
    
    # 如果没有找到私有IP，添加默认的本地IP
    if not ip_addresses:
        ip_addresses.append("127.0.0.1")
        
    return ip_addresses

def uuid_generator(with_dash: bool = True) -> str:
    """生成UUID"""
    if with_dash:
        return str(uuid.uuid4())
    else:
        return str(uuid.uuid4()).replace("-", "")

def unix_timestamp() -> int:
    """获取Unix时间戳"""
    import time
    return int(time.time())

def md5(text: str) -> str:
    """计算MD5哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def is_base64_data(data: str) -> bool:
    """检查是否为BASE64数据"""
    if not isinstance(data, str):
        return False
    return data.startswith("data:")

def extract_base64_data_format(data: str) -> str:
    """提取BASE64数据格式"""
    if not is_base64_data(data):
        return ""
    return data.split(";")[0].split(":")[1]

def remove_base64_data_header(data: str) -> str:
    """移除BASE64数据头部"""
    if not is_base64_data(data):
        return data
    return data.split(",")[1]