"""
WebView应用主程序
使用pywebview展示前端界面，支持Python后端与前端通信
"""

import webview
import os
import sys
from pathlib import Path

# 导入数据库模块
from database import init_database, close_database, logger, get_config, set_config, get_all_configs, add_account, batch_add_accounts, delete_accounts, get_accounts_with_usage, add_record


class API:
    """后端API类，提供前端调用的Python方法"""

    def __init__(self):
        self.window = None

    def set_window(self, window):
        """设置窗口对象，用于前端调用"""
        self.window = window

    def get_info(self):
        """获取应用信息"""
        logger.info("获取应用信息")
        return {
            'app_name': 'Jimeng Scripts',
            'version': '1.0.0',
            'platform': sys.platform
        }

    def log_message(self, message):
        """记录来自前端的消息"""
        logger.info(f"[前端消息] {message}")
        print(f"[前端消息] {message}")
        return f"已记录: {message}"

    def perform_calculation(self, a, b, operation):
        """执行计算操作"""
        try:
            logger.info(f"执行计算: {a} {operation} {b}")
            if operation == 'add':
                result = a + b
            elif operation == 'subtract':
                result = a - b
            elif operation == 'multiply':
                result = a * b
            elif operation == 'divide':
                if b == 0:
                    logger.warning("尝试被0除")
                    return {'success': False, 'error': '不能被0整除'}
                result = a / b
            else:
                logger.warning(f"未知操作: {operation}")
                return {'success': False, 'error': '未知操作'}

            logger.info(f"计算结果: {result}")
            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f"计算出错: {e}")
            return {'success': False, 'error': str(e)}

    def get_config(self, key):
        """获取配置值"""
        logger.info(f"获取配置: {key}")
        return get_config(key)

    def set_config(self, key, value):
        """设置配置值"""
        logger.info(f"设置配置: {key} = {value}")
        set_config(key, value)
        return {'success': True}

    def get_all_configs(self):
        """获取所有配置"""
        logger.info("获取所有配置")
        return get_all_configs()

    def add_account(self, token, points):
        """添加账号"""
        logger.info(f"添加账号: {token}")
        return add_account(token, points)

    def batch_add_accounts(self, tokens, points):
        """批量添加账号"""
        logger.info(f"批量添加账号，数量: {len(tokens)}")
        return batch_add_accounts(tokens, points)

    def delete_accounts(self, account_ids):
        """删除账号"""
        logger.info(f"删除账号，IDs: {account_ids}")
        return delete_accounts(account_ids)

    def get_accounts_with_usage(self):
        """获取所有账号及其使用情况"""
        logger.info("获取账号列表及使用情况")
        return get_accounts_with_usage()

    def add_record(self, account_id, record_type):
        """添加记录"""
        logger.info(f"添加记录: 账号ID={account_id}, 类型={record_type}")
        return add_record(account_id, record_type)


def get_static_path():
    """获取静态文件目录路径"""
    # 如果是打包后的exe，使用sys._MEIPASS
    if getattr(sys, 'frozen', False):
        # 使用 getattr 来避免静态检查错误
        meipass = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
        static_path = os.path.join(meipass, 'app', 'static')
    else:
        # 开发环境
        static_path = os.path.join(os.path.dirname(__file__), 'static')

    return static_path


def main():
    """主函数"""
    # 初始化数据库
    if not init_database():
        logger.error("数据库初始化失败，程序退出")
        sys.exit(1)
    
    logger.info("应用启动")

    # 获取静态文件路径
    static_path = get_static_path()
    html_file = os.path.join(static_path, 'index.html')

    # 检查HTML文件是否存在
    if not os.path.exists(html_file):
        logger.error(f"错误: 找不到HTML文件: {html_file}")
        sys.exit(1)

    # 创建API实例
    api = API()

    # 创建WebView窗口，设置为全屏自适应
    window = webview.create_window(
        title='Jimeng Scripts',
        url=f'file://{html_file}',
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
        background_color='#ffffff',
        min_size=(800, 600)
    )

    # 将窗口对象传递给API
    api.set_window(window)

    try:
        # 启动应用
        webview.start(debug=False)
    finally:
        # 关闭数据库连接
        close_database()
        logger.info("应用关闭")


if __name__ == '__main__':
    main()