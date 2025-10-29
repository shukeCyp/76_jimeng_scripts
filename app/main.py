"""
WebView应用主程序
使用pywebview展示前端界面，支持Python后端与前端通信
"""

import webview
import os
import sys
from pathlib import Path


class API:
    """后端API类，提供前端调用的Python方法"""

    def __init__(self):
        self.window = None

    def set_window(self, window):
        """设置窗口对象，用于前端调用"""
        self.window = window

    def get_info(self):
        """获取应用信息"""
        return {
            'app_name': 'WebView Application',
            'version': '1.0.0',
            'platform': sys.platform
        }

    def log_message(self, message):
        """记录来自前端的消息"""
        print(f"[前端消息] {message}")
        return f"已记录: {message}"

    def perform_calculation(self, a, b, operation):
        """执行计算操作"""
        try:
            if operation == 'add':
                result = a + b
            elif operation == 'subtract':
                result = a - b
            elif operation == 'multiply':
                result = a * b
            elif operation == 'divide':
                if b == 0:
                    return {'success': False, 'error': '不能被0整除'}
                result = a / b
            else:
                return {'success': False, 'error': '未知操作'}

            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def get_static_path():
    """获取静态文件目录路径"""
    # 如果是打包后的exe，使用sys._MEIPASS
    if getattr(sys, 'frozen', False):
        static_path = os.path.join(sys._MEIPASS, 'app', 'static')
    else:
        # 开发环境
        static_path = os.path.join(os.path.dirname(__file__), 'static')

    return static_path


def main():
    """主函数"""
    # 获取静态文件路径
    static_path = get_static_path()
    html_file = os.path.join(static_path, 'index.html')

    # 检查HTML文件是否存在
    if not os.path.exists(html_file):
        print(f"错误: 找不到HTML文件: {html_file}")
        sys.exit(1)

    # 创建API实例
    api = API()

    # 创建WebView窗口
    window = webview.create_window(
        title='WebView Application',
        url=f'file://{html_file}',
        js_api=api,
        width=1000,
        height=700,
        resizable=True,
        background_color='#ffffff'
    )

    # 将窗口对象传递给API
    api.set_window(window)

    # 启动应用
    webview.start(debug=False)


if __name__ == '__main__':
    main()
