import os
import sys
import json
import logging
from typing import Any, Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add the lib directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from .config import config
from .logger import logger

class Request:
    """请求类"""
    def __init__(self, handler):
        self.handler = handler
        self.method = handler.command
        self.path = handler.path
        self.headers = dict(handler.headers)
        self.query_params = parse_qs(urlparse(self.path).query)
        self.body = None
        if self.method in ['POST', 'PUT', 'PATCH']:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                self.body = handler.rfile.read(content_length)
                # 尝试解析JSON
                try:
                    self.json = json.loads(self.body.decode('utf-8'))
                except:
                    self.json = None

class SimpleResponse:
    """简单响应类"""
    def __init__(self, data=None, status_code=200):
        self.data = data
        self.status_code = status_code

class Server:
    """简化版服务器类"""
    
    def __init__(self):
        """初始化服务器"""
        self.routes = {}
        logger.success("Server initialized")
    
    def attach_routes(self, routes: List[Dict[str, Any]]):
        """附加路由"""
        for route in routes:
            prefix = route.get("prefix", "")
            
            for method in route:
                if method == "prefix":
                    continue
                
                if not isinstance(route[method], dict):
                    logger.warn(f"Router {prefix} {method} invalid")
                    continue
                
                for uri in route[method]:
                    handler = route[method][uri]
                    full_uri = f"{prefix}{uri}"
                    method_key = method.upper()
                    
                    if full_uri not in self.routes:
                        self.routes[full_uri] = {}
                    
                    self.routes[full_uri][method_key] = handler
            
            logger.info(f"Route {config.service.urlPrefix or ''}{prefix} attached")
    
    def listen(self):
        """启动监听"""
        host = config.service.host
        port = config.service.port
        
        # 保存路由信息到类变量
        Server._routes = self.routes
        
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle_request('GET')
            
            def do_POST(self):
                self._handle_request('POST')
            
            def do_PUT(self):
                self._handle_request('PUT')
            
            def do_DELETE(self):
                self._handle_request('DELETE')
            
            def _handle_request(self, method):
                # 简单路由匹配
                path = urlparse(self.path).path
                
                # 处理根路径
                if path == "/" and method == "GET":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response_data = {
                        "message": "Welcome to Jimeng API",
                        "version": "1.3.0"
                    }
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 处理ping路径
                if path == "/ping" and method == "GET":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response_data = {"message": "pong"}
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                
                # 处理其他路由
                if path in Server._routes and method in Server._routes[path]:
                    try:
                        request = Request(self)
                        handler = Server._routes[path][method]
                        result = handler(request)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        if isinstance(result, SimpleResponse):
                            response_data = result.data
                        else:
                            response_data = result
                            
                        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        error_data = {"error": str(e)}
                        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    error_data = {"error": "Not Found"}
                    self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
        
        # 创建HTTP服务器
        server = HTTPServer((host, port), RequestHandler)
        
        logger.success(f"Server listening on port {port} ({host})")
        server.serve_forever()

# 全局服务器实例
server = Server()