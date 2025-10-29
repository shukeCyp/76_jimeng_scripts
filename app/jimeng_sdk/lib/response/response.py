import time
import json
from typing import Any, Dict, Optional
from flask import Response as FlaskResponse, jsonify

from .failure_body import FailureBody

class Response:
    """响应类"""
    
    def __init__(self, body: Any = None, options: Optional[Dict[str, Any]] = None):
        """初始化响应"""
        self.body = body
        self.options = options or {}
        self.time = int(time.time() * 1000)  # 毫秒时间戳
    
    def to_flask_response(self) -> FlaskResponse:
        """转换为Flask响应"""
        # 处理不同的响应体类型
        if isinstance(self.body, FailureBody):
            response_data = {
                "code": self.body.code,
                "message": self.body.message,
                "data": self.body.data,
                "time": self.body.time
            }
            status_code = 400  # 默认错误状态码
        elif isinstance(self.body, dict):
            response_data = self.body
            status_code = 200
        elif hasattr(self.body, '__dict__'):
            response_data = self.body.__dict__
            status_code = 200
        else:
            response_data = {"data": self.body}
            status_code = 200
        
        # 创建Flask响应
        flask_response = jsonify(response_data)
        flask_response.status_code = status_code
        
        # 设置响应头
        if "headers" in self.options:
            for key, value in self.options["headers"].items():
                flask_response.headers[key] = value
        
        # 设置内容类型
        if "type" in self.options:
            content_type = self.options["type"]
            if content_type == "html":
                flask_response.headers["Content-Type"] = "text/html"
            elif content_type == "json":
                flask_response.headers["Content-Type"] = "application/json"
        
        return flask_response
    
    @staticmethod
    def is_instance(obj) -> bool:
        """检查对象是否为Response实例"""
        return isinstance(obj, Response)