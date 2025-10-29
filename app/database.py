"""
数据库模块，使用 SQLite 和 Peewee ORM
"""

import os
import sys
from pathlib import Path
from peewee import *
import platform
from datetime import datetime

# 确保正确导入 loguru
try:
    from loguru import logger as loguru_logger
    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    import logging
    logging.basicConfig(level=logging.INFO)
    std_logger = logging.getLogger(__name__)
    # 创建一个简单的包装器来模拟 loguru 接口
    class LoggerWrapper:
        def __init__(self, logger):
            self._logger = logger
            
        def info(self, msg):
            self._logger.info(msg)
            
        def error(self, msg):
            self._logger.error(msg)
            
        def warning(self, msg):
            self._logger.warning(msg)
            
        def debug(self, msg):
            self._logger.debug(msg)
            
        # 添加空的 remove 和 add 方法以避免错误
        def remove(self):
            pass
            
        def add(self, *args, **kwargs):
            pass
            
    loguru_logger = LoggerWrapper(std_logger)


def get_app_data_dir(app_name):
    """
    获取应用数据目录路径
    在 AppData 目录下创建 jimeng_script 文件夹
    """
    system = platform.system()
    if system == "Windows":
        # Windows 系统使用 AppData
        base_dir = os.path.expanduser("~\\AppData\\Roaming")
    elif system == "Darwin":  # macOS
        # macOS 使用 Application Support
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:
        # Linux 和其他系统使用 .local/share
        base_dir = os.path.expanduser("~/.local/share")
    
    app_dir = os.path.join(base_dir, app_name)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def setup_logging():
    """设置日志系统"""
    # 获取应用数据目录
    app_data_dir = get_app_data_dir("jimeng_script")
    
    # 创建 logs 目录
    logs_dir = os.path.join(app_data_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # 如果使用 loguru
    if HAS_LOGURU:
        # 配置 loguru
        loguru_logger.remove()  # 移除默认的日志处理器
        
        # 添加文件日志处理器
        log_file = os.path.join(logs_dir, "app.log")
        loguru_logger.add(
            log_file,
            rotation="10 MB",  # 日志文件最大10MB
            retention="30 days",  # 保留30天的日志
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            level="INFO"
        )
        
        # 添加控制台日志处理器（调试用）
        loguru_logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        return loguru_logger
    else:
        # 使用标准 logging 配置
        import logging
        log_file = os.path.join(logs_dir, "app.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filemode='a'
        )
        
        return loguru_logger


def get_database():
    """获取数据库实例"""
    # 获取应用数据目录
    app_data_dir = get_app_data_dir("jimeng_script")
    
    # 创建 database 目录
    db_dir = os.path.join(app_data_dir, "database")
    os.makedirs(db_dir, exist_ok=True)
    
    # 数据库文件路径
    db_path = os.path.join(db_dir, "app.db")
    
    # 创建数据库实例
    db = SqliteDatabase(db_path)
    return db


# 初始化日志系统
logger = setup_logging()

# 获取数据库实例
db = get_database()


# 定义基础模型类
class BaseModel(Model):
    class Meta:
        database = db


# 配置模型 - 存储键值对配置
class Config(BaseModel):
    key = CharField(unique=True)
    value = TextField()
    description = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


# 账号模型
class JimengAccount(BaseModel):
    token = CharField(unique=True)
    points = IntegerField(default=0)  # 积分
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


# 记录模型
class JimengRecord(BaseModel):
    account = ForeignKeyField(JimengAccount, backref='records')
    type = IntegerField()  # 1代表图片，2代表视频
    time = DateTimeField(default=datetime.now)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


def init_database():
    """初始化数据库"""
    try:
        # 连接数据库
        db.connect()
        
        # 创建表
        db.create_tables([Config, JimengAccount, JimengRecord], safe=True)
        
        # 初始化默认配置
        init_default_configs()
        
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def init_default_configs():
    """初始化默认配置"""
    default_configs = [
        {'key': 'api_key', 'value': '', 'description': 'API密钥'},
        {'key': 'api_proxy', 'value': '', 'description': 'API代理地址'},
        {'key': 'model', 'value': '', 'description': '模型名称'},
        {'key': 'max_threads', 'value': '5', 'description': '最大线程数'},
        {'key': 'daily_video_limit', 'value': '2', 'description': '单账号单日视频数'},
        {'key': 'daily_image_limit', 'value': '10', 'description': '单账号单日图片数'}
    ]
    
    for config_data in default_configs:
        # 使用 get_or_create 确保配置项存在
        query = Config.select().where(Config.key == config_data['key'])
        if query.exists():
            # 配置已存在，更新描述（如果需要）
            config = query.first()
            if config.description != config_data['description']:
                config.description = config_data['description']
                config.save()
        else:
            # 配置不存在，创建新配置
            Config.create(
                key=config_data['key'],
                value=config_data['value'],
                description=config_data['description']
            )
    
    logger.info("默认配置初始化完成")


def get_config(key, default=None):
    """获取配置值"""
    try:
        config = Config.get(Config.key == key)
        return config.value
    except Exception:
        return default


def set_config(key, value):
    """设置配置值"""
    try:
        config = Config.get(Config.key == key)
        config.value = str(value)
        config.save()
        logger.info(f"配置已更新: {key} = {value}")
        return {'success': True}
    except Exception:
        try:
            Config.create(key=key, value=str(value))
            logger.info(f"配置已创建: {key} = {value}")
            return {'success': True}
        except Exception as e:
            logger.error(f"配置保存失败: {key} = {value}, 错误: {e}")
            return {'success': False, 'error': str(e)}


def get_all_configs():
    """获取所有配置"""
    configs = {}
    try:
        for config in Config.select():
            configs[config.key] = config.value
        logger.info(f"成功获取所有配置，共{len(configs)}项")
        return configs
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return configs


def add_account(token, points=0):
    """添加账号"""
    try:
        account = JimengAccount.create(token=token, points=points)
        logger.info(f"账号添加成功: {token}")
        return {'success': True, 'account_id': account.id}
    except Exception as e:
        logger.error(f"添加账号失败: {e}")
        return {'success': False, 'error': str(e)}


def batch_add_accounts(tokens, points=0):
    """批量添加账号"""
    try:
        added_accounts = []
        failed_accounts = []
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
                
            try:
                account = JimengAccount.create(token=token, points=points)
                added_accounts.append(account.id)
                logger.info(f"账号添加成功: {token}")
            except IntegrityError:
                failed_accounts.append(token)
                logger.warning(f"账号已存在，跳过: {token}")
            except Exception as e:
                failed_accounts.append(token)
                logger.error(f"添加账号失败 {token}: {e}")
        
        return {
            'success': True,
            'added_count': len(added_accounts),
            'failed_count': len(failed_accounts),
            'added_accounts': added_accounts,
            'failed_accounts': failed_accounts
        }
    except Exception as e:
        logger.error(f"批量添加账号失败: {e}")
        return {'success': False, 'error': str(e)}


def delete_accounts(account_ids):
    """删除指定ID的账号"""
    try:
        # 删除相关的记录
        JimengRecord.delete().where(JimengRecord.account << account_ids).execute()
        
        # 删除账号
        deleted_count = JimengAccount.delete().where(JimengAccount.id << account_ids).execute()
        
        logger.info(f"成功删除 {deleted_count} 个账号")
        return {'success': True, 'deleted_count': deleted_count}
    except Exception as e:
        logger.error(f"删除账号失败: {e}")
        return {'success': False, 'error': str(e)}


def get_accounts_with_usage():
    """获取所有账号及其当日使用次数"""
    try:
        accounts = []
        today = datetime.now().date()
        
        for account in JimengAccount.select():
            # 计算当日图片使用次数
            image_count = JimengRecord.select().where(
                (JimengRecord.account == account) &
                (JimengRecord.type == 1) &
                (fn.date(JimengRecord.time) == today)
            ).count()
            
            # 计算当日视频使用次数
            video_count = JimengRecord.select().where(
                (JimengRecord.account == account) &
                (JimengRecord.type == 2) &
                (fn.date(JimengRecord.time) == today)
            ).count()
            
            accounts.append({
                'id': account.id,
                'token': account.token,
                'points': account.points,
                'image_count': image_count,
                'video_count': video_count,
                'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': account.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return accounts
    except Exception as e:
        logger.error(f"获取账号列表失败: {e}")
        return []


def add_record(account_id, record_type):
    """添加记录"""
    try:
        # 检查账号是否存在
        account = JimengAccount.get_by_id(account_id)
        record = JimengRecord.create(account=account, type=record_type, time=datetime.now())
        logger.info(f"记录添加成功: 账号ID={account_id}, 类型={record_type}")
        return {'success': True, 'record_id': record.id}
    except DoesNotExist:
        logger.error(f"账号不存在: ID={account_id}")
        return {'success': False, 'error': '账号不存在'}
    except Exception as e:
        logger.error(f"添加记录失败: {e}")
        return {'success': False, 'error': str(e)}


def close_database():
    """关闭数据库连接"""
    try:
        if not db.is_closed():
            db.close()
            logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


# 程序退出时确保数据库连接关闭
import atexit
atexit.register(close_database)