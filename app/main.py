#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebView应用主程序
使用pywebview展示前端界面，支持Python后端与前端通信
"""

import webview
import os
import sys
from pathlib import Path
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import json

# 导入数据库模块
from database import init_database, close_database, logger, get_config, set_config, get_all_configs, add_account, batch_add_accounts, delete_accounts, get_accounts_with_usage, add_record

# 导入账号工具类
from accounts_utils import get_image_account, get_video_account

# 导入即梦工具类
from jimeng_utils import generate_image, generate_video, generate_sence

# 全局线程池变量
thread_pool = None
handless = False

# 全局字典用于存储生成的图片信息
generated_images_dict = {}


class API:
    """后端API类，提供前端调用的Python方法"""

    def __init__(self):
        self.window = None

    def set_window(self, window):
        """设置窗口对象，用于前端调用"""
        self.window = window

    def toggle_headless_mode(self):
        """切换无头模式"""
        global handless
        handless = not handless
        logger.info(f"无头模式已切换为: {handless}")
        return {'success': True, 'handless': handless}

    def submit_task_to_thread_pool(self, func, *args, **kwargs):
        """提交任务到线程池执行"""
        global thread_pool
        if thread_pool:
            future = thread_pool.submit(func, *args, **kwargs)
            return future
        else:
            # 如果线程池不可用，直接在当前线程执行
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                raise e

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

    def add_account(self, username, password=None, cookies=None):
        """添加账号"""
        logger.info(f"添加账号: {username}")
        return add_account(username, password, cookies)

    def batch_add_accounts(self, accounts_data):
        """批量添加账号"""
        logger.info(f"批量添加账号，数量: {len(accounts_data)}")
        return batch_add_accounts(accounts_data)

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

    def get_generated_images(self, unique_id):
        """获取指定unique_id的生成图片列表"""
        logger.info(f"获取生成图片列表，unique_id: {unique_id}")
        if unique_id in generated_images_dict:
            return {'success': True, 'images': generated_images_dict[unique_id]}
        else:
            return {'success': True, 'images': []}

    def get_generated_videos(self, unique_id):
        """获取指定unique_id的生成视频列表"""
        logger.info(f"获取生成视频列表，unique_id: {unique_id}")
        global generated_videos_dict
        if 'generated_videos_dict' not in globals():
            generated_videos_dict = {}
        if unique_id in generated_videos_dict:
            return {'success': True, 'videos': generated_videos_dict[unique_id]}
        else:
            return {'success': True, 'videos': []}

    def select_folder(self):
        """选择文件夹"""
        try:
            # 使用 pywebview 提供的文件选择功能
            if self.window:
                # 使用 pywebview 的文件选择对话框（使用新的 API）
                result = self.window.create_file_dialog(webview.FileDialog.FOLDER)
                logger.info(f"文件夹选择结果: {result}, 类型: {type(result)}")
                
                if result:
                    # 处理返回的结果（可能是元组、列表或单个路径）
                    folder_path = ""
                    if isinstance(result, tuple):
                        # 如果是元组，取第一个元素
                        folder_path = result[0] if len(result) > 0 else ""
                        logger.info(f"从元组中获取文件夹路径: {folder_path}")
                    elif isinstance(result, list) and len(result) > 0:
                        folder_path = result[0]
                        logger.info(f"从列表中获取文件夹路径: {folder_path}")
                    elif isinstance(result, str):
                        folder_path = result
                        logger.info(f"直接获取文件夹路径: {folder_path}")
                    elif isinstance(result, os.PathLike):
                        folder_path = str(result)
                        logger.info(f"从PathLike对象获取文件夹路径: {folder_path}")
                    else:
                        logger.error(f"无效的文件夹路径类型: {type(result)}, 值: {result}")
                        return {'success': False, 'error': f'无效的文件夹路径类型: {type(result)}'}
                    
                    # 检查路径是否为空
                    if not folder_path:
                        logger.error("文件夹路径为空")
                        return {'success': False, 'error': '文件夹路径为空'}
                    
                    # 验证路径是否存在
                    if not os.path.exists(folder_path):
                        logger.error(f"文件夹路径不存在: {folder_path}")
                        return {'success': False, 'error': f'文件夹路径不存在: {folder_path}'}
                    
                    # 验证是否为文件夹
                    if not os.path.isdir(folder_path):
                        logger.error(f"路径不是文件夹: {folder_path}")
                        return {'success': False, 'error': f'路径不是文件夹: {folder_path}'}
                    
                    # 获取文件夹中的图片文件
                    self.debug_folder_structure(folder_path)  # 调试文件夹结构
                    files = self._get_folder_images(folder_path)
                    
                    return {'success': True, 'folder_path': folder_path, 'files': files}
                else:
                    logger.info("用户未选择文件夹")
                    return {'success': False, 'error': '未选择文件夹'}
            else:
                logger.error("窗口对象未初始化")
                return {'success': False, 'error': '窗口对象未初始化'}
        except Exception as e:
            logger.error(f"选择文件夹失败: {e}")
            return {'success': False, 'error': str(e)}

    def _get_folder_images(self, folder_path):
        """获取文件夹中的图片文件"""
        import os
        import glob
        import json
        
        logger.info(f"开始遍历文件夹: {folder_path}")
        
        # 验证文件夹路径是否存在
        if not os.path.exists(folder_path):
            logger.error(f"文件夹路径不存在: {folder_path}")
            return []
        
        # 验证是否为文件夹
        if not os.path.isdir(folder_path):
            logger.error(f"路径不是文件夹: {folder_path}")
            return []
        
        # 查找 images 文件夹
        images_folder = os.path.join(folder_path, "images")
        items_folder = os.path.join(folder_path, "items")
        
        logger.info(f"images文件夹路径: {images_folder}")
        logger.info(f"items文件夹路径: {items_folder}")
        
        if not os.path.exists(images_folder):
            logger.error(f"未找到 images 文件夹: {images_folder}")
            return []
        
        if not os.path.exists(items_folder):
            logger.error(f"未找到 items 文件夹: {items_folder}")
            return []
        
        files = []
        
        # 遍历 images 文件夹中的所有子文件夹
        try:
            subdirs = os.listdir(images_folder)
            logger.info(f"images文件夹中的子文件夹数量: {len(subdirs)}")
            
            for subdir in subdirs:
                subdir_path = os.path.join(images_folder, subdir)
                if os.path.isdir(subdir_path):
                    logger.info(f"处理子文件夹: {subdir_path}")
                    
                    # 查找该子文件夹中的所有图片文件
                    image_files = []
                    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']:
                        pattern = os.path.join(subdir_path, ext)
                        image_files.extend(glob.glob(pattern))
                    
                    logger.info(f"子文件夹 {subdir} 中找到图片文件数量: {len(image_files)}")
                    
                    if image_files:
                        # 取第一张图片作为默认主图
                        main_image = image_files[0]
                        file_name = os.path.basename(subdir_path)
                        
                        logger.info(f"子文件夹 {subdir} 的主图: {main_image}")
                        
                        # 查找对应的 JSON 文件（如果存在）
                        json_file = os.path.join(items_folder, f"{subdir}.json")
                        title = subdir  # 默认使用文件夹名作为标题
                        if os.path.exists(json_file):
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    # 尝试从 JSON 中获取标题
                                    if isinstance(data, dict):
                                        title = data.get('title', data.get('name', subdir))
                                logger.info(f"从JSON文件 {json_file} 中获取标题: {title}")
                            except Exception as e:
                                logger.warning(f"读取 JSON 文件失败 {json_file}: {e}")
                        else:
                            logger.info(f"未找到对应的JSON文件: {json_file}")
                        
                        # 添加文件夹路径信息
                        file_info = {
                            'name': title,
                            'main_image': main_image,
                            'folder_path': subdir_path,  # 保存文件夹路径
                            'generated_images': [],  # 待生成的模特图
                            'generated_videos': []   # 待生成的视频
                        }
                        
                        files.append(file_info)
                        logger.info(f"添加文件信息: {file_info}")
                    else:
                        logger.info(f"子文件夹 {subdir} 中没有找到图片文件")
        except Exception as e:
            logger.error(f"遍历 images 文件夹时出错: {e}")
            return []
        
        logger.info(f"总共找到 {len(files)} 个文件夹")
        return files

    def get_images_in_folder(self, folder_path):
        """获取文件夹中的所有图片"""
        import os
        import glob
        
        logger.info(f"获取文件夹中的图片: {folder_path}")
        
        # 验证文件夹路径是否存在
        if not os.path.exists(folder_path):
            logger.error(f"文件夹路径不存在: {folder_path}")
            return {'success': False, 'error': '文件夹路径不存在'}
        
        # 验证是否为文件夹
        if not os.path.isdir(folder_path):
            logger.error(f"路径不是文件夹: {folder_path}")
            return {'success': False, 'error': '路径不是文件夹'}
        
        # 查找所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']:
            pattern = os.path.join(folder_path, ext)
            image_files.extend(glob.glob(pattern))
        
        logger.info(f"找到图片文件数量: {len(image_files)}")
        return {'success': True, 'images': image_files}

    def generate_image_with_id(self, image_path, index, unique_id, prompt=None):
        """生成图片（使用图生图方式），带唯一标识符"""
        logger.info(f"[DEBUG] generate_image_with_id called with image_path={image_path}, index={index}, unique_id={unique_id}, prompt={prompt}")
        
        # 确保prompt不为None
        if prompt is None:
            prompt = ""
        
        # 使用线程池执行图片生成任务
        def _generate_image_task():
            try:
                # 获取可用的图片账号
                account_info = get_image_account()
                logger.info("使用图片账号生成图片")
                
                # 检查是否有可用账号
                if not account_info:
                    error_msg = "没有可用的账号或均已达到使用上限"
                    logger.error(error_msg)
                    return {'success': False, 'error': error_msg}
                
                # 从账号信息中提取认证信息
                username = account_info.get('username')
                password = account_info.get('password')
                cookies = account_info.get('cookies')
                account_id = account_info.get('id')  # 获取账号ID
                
                # 调用 jimeng_image_util.py 中的图片生成函数
                import asyncio
                from jimeng_image_util import generate_image as jimeng_generate_image
                
                # 使用全局的 handless 变量控制是否使用无头模式
                global handless
                
                # 使用 asyncio.run() 运行异步函数
                try:
                    # 注意：这里需要在新的事件循环中运行，因为我们在同步函数中调用异步函数
                    result = asyncio.run(jimeng_generate_image(
                        cookies=cookies,
                        username=username,
                        password=password,
                        prompt=prompt,
                        image_path=image_path,
                        headless=not handless,  # 如果 handless 为 False，则 headless 参数为 True（无头模式）
                        account_id=account_id  # 传递账号ID用于保存cookies
                    ))
                except Exception as e:
                    logger.error(f"调用图片生成函数失败: {e}")
                    return {'success': False, 'error': str(e)}
                
                # 处理生成结果
                if result.get('success'):
                    logger.info(f"图片生成成功: {result}")
                    # 提取生成的图片URL并下载到本地
                    image_urls = result.get('image_urls', [])
                    local_image_paths = []
                    
                    if image_urls:
                        import os
                        import requests
                        from datetime import datetime
                        
                        # 创建保存图片的目录
                        app_dir = os.path.dirname(os.path.dirname(__file__))
                        save_dir = os.path.join(app_dir, "generated_images", datetime.now().strftime("%Y%m%d_%H%M%S"))
                        os.makedirs(save_dir, exist_ok=True)
                        logger.info(f"[DEBUG] Created save directory: {save_dir}")
                        
                        for i, image_url in enumerate(image_urls):
                            try:
                                # 下载图片（带重试逻辑）
                                max_retries = 10  # 重试次数
                                retry_count = 0
                                
                                while retry_count < max_retries:
                                    try:
                                        response = requests.get(image_url, timeout=30)
                                        response.raise_for_status()
                                        
                                        # 生成本地文件名
                                        file_extension = ".png"  # 默认扩展名
                                        if 'content-type' in response.headers:
                                            content_type = response.headers['content-type']
                                            if 'jpeg' in content_type or 'jpg' in content_type:
                                                file_extension = ".jpg"
                                            elif 'png' in content_type:
                                                file_extension = ".png"
                                            elif 'webp' in content_type:
                                                file_extension = ".webp"
                                        
                                        local_filename = f"generated_image_{i+1}{file_extension}"
                                        local_filepath = os.path.join(save_dir, local_filename)
                                        
                                        # 保存图片到本地
                                        with open(local_filepath, 'wb') as f:
                                            f.write(response.content)
                                        
                                        # 保存本地路径
                                        local_image_paths.append(local_filepath)
                                        logger.info(f"图片已保存到: {local_filepath}")
                                        break  # 成功下载，跳出重试循环
                                    except Exception as e:
                                        retry_count += 1
                                        logger.warning(f"下载图片失败 (尝试 {retry_count}/{max_retries}): {e}")
                                        if retry_count >= max_retries:
                                            raise e  # 达到最大重试次数，抛出异常
                                        time.sleep(2)  # 等待2秒后重试
                            except Exception as e:
                                logger.error(f"下载图片失败: {e}")
                                # 如果下载失败，仍然添加URL
                                local_image_paths.append(image_url)
                    
                    # 添加图片生成记录到数据库
                    try:
                        # 获取使用的账号ID
                        if account_id:
                            # 添加图片生成记录
                            add_record(account_id, 1)  # 1代表图片
                            logger.info(f"图片生成记录已添加，账号ID: {account_id}")
                        else:
                            logger.warning("无法获取账号ID，跳过记录添加")
                    except Exception as e:
                        logger.error(f"添加图片生成记录失败: {e}")
                    
                    # 将本地图片路径传递给前端，并指定对应的item索引和唯一标识符
                    if self.window:
                        # 保存生成的图片路径到全局字典
                        for path in local_image_paths:
                            self.add_generated_image(unique_id, path)
                        
                        # 转义路径中的特殊字符
                        escaped_paths = [path.replace('"', '\\"') for path in local_image_paths]
                        paths_js_array = str(escaped_paths)
                        # 传递当前生成索引和唯一标识符给前端
                        logger.info(f"[DEBUG] Calling frontend handleGeneratedImagesForItem with paths={paths_js_array}, index={index}, unique_id={unique_id}")
                        self.window.evaluate_js(f"handleGeneratedImagesForItem({paths_js_array}, {index}, '{unique_id}')")
                    
                    return {'success': True, 'message': '图片生成任务已启动'}
                else:
                    error_msg = result.get('error', '未知错误')
                    logger.error(f"图片生成失败: {error_msg}")
                    return {'success': False, 'error': error_msg}
            except Exception as e:
                logger.error(f"生成图片失败: {e}")
                return {'success': False, 'error': str(e)}
        
        # 提交任务到线程池并立即返回一个可序列化的结果
        try:
            future = self.submit_task_to_thread_pool(_generate_image_task)
            # 不直接返回future对象，而是返回一个表示任务已提交的消息
            # 如果future是一个Future对象，我们不直接返回它
            if hasattr(future, 'add_done_callback'):
                # 这是一个Future对象，我们不直接返回它
                return {'success': True, 'message': '图片生成任务已启动'}
            else:
                # 这是直接执行的结果（线程池不可用时）
                return future
        except Exception as e:
            logger.error(f"提交图片生成任务失败: {e}")
            return {'success': False, 'error': str(e)}

    def generate_image(self, image_path, index, prompt=None):
        """生成图片（使用图生图方式）- 为了向后兼容保留此方法"""
        # 生成一个临时的unique_id用于此次调用
        import uuid
        unique_id = str(uuid.uuid4())
        logger.info(f"[DEBUG] generate_image called, generating temporary unique_id: {unique_id}")
        return self.generate_image_with_id(image_path, index, unique_id, prompt)

    def generate_video(self, image_path, prompt=None):
        """生成视频"""
        try:
            import os  # 导入os模块
            
            # 获取视频时长配置
            video_duration = get_config('video_duration', '5')  # 默认5秒
            logger.info(f"视频时长配置: {video_duration}秒")
            
            # 移除视频生成方式配置，只使用图生视频
            # 移除是否使用国内账号的配置，只使用国际账号
            
            # 将秒转换为毫秒
            duration_ms = int(video_duration) * 1000
            
            # 获取可用账号（用于视频生成）
            account_info = get_video_account()
            logger.info("使用视频账号生成视频")
            
            # 检查是否有可用账号
            if not account_info:
                error_msg = "没有可用的账号或均已达到使用上限"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            # 从账号信息中提取认证信息
            username = account_info.get('username')
            password = account_info.get('password')
            cookies = account_info.get('cookies')
            account_id = account_info.get('id')  # 获取账号ID

            # 图生视频
            if image_path and os.path.exists(image_path):
                logger.info(f"开始生成图生视频，提示词: {prompt}，时长: {video_duration}秒")
                # 调用 jimeng_video_util.py 中的视频生成函数
                import asyncio
                from jimeng_video_util import generate_video as jimeng_generate_video
                
                # 使用全局的 handless 变量控制是否使用无头模式
                global handless
                
                # 使用 asyncio.run() 运行异步函数
                try:
                    # 注意：这里需要在新的事件循环中运行，因为我们在同步函数中调用异步函数
                    result = asyncio.run(jimeng_generate_video(
                        cookies=cookies,
                        username=username,
                        password=password,
                        prompt=prompt,
                        seconds=int(video_duration),
                        image_path=image_path,
                        headless=not handless,  # 如果 handless 为 False，则 headless 参数为 True（无头模式）
                        account_id=account_id  # 传递账号ID用于保存cookies
                    ))
                    
                    # 处理生成结果
                    if result.get('success'):
                        logger.info(f"视频生成成功: {result}")
                        # 提取生成的视频URL并下载到本地
                        video_url = result.get('video_url')
                        local_video_path = None
                        
                        if video_url:
                            try:
                                import os
                                import requests
                                from datetime import datetime
                                
                                # 创建保存视频的目录
                                app_dir = os.path.dirname(os.path.dirname(__file__))
                                save_dir = os.path.join(app_dir, "generated_videos", datetime.now().strftime("%Y%m%d_%H%M%S"))
                                os.makedirs(save_dir, exist_ok=True)
                                logger.info(f"[DEBUG] Created save directory: {save_dir}")
                                
                                # 下载视频（带重试逻辑）
                                max_retries = 10  # 重试次数
                                retry_count = 0
                                
                                while retry_count < max_retries:
                                    try:
                                        response = requests.get(video_url, timeout=30)
                                        response.raise_for_status()
                                        
                                        # 生成本地文件名
                                        file_extension = ".mp4"  # 默认扩展名
                                        if 'content-type' in response.headers:
                                            content_type = response.headers['content-type']
                                            if 'mp4' in content_type:
                                                file_extension = ".mp4"
                                            elif 'mov' in content_type:
                                                file_extension = ".mov"
                                            elif 'avi' in content_type:
                                                file_extension = ".avi"
                                        
                                        local_filename = f"generated_video{file_extension}"
                                        local_video_path = os.path.join(save_dir, local_filename)
                                        
                                        # 保存视频到本地
                                        with open(local_video_path, 'wb') as f:
                                            f.write(response.content)
                                        
                                        logger.info(f"视频已保存到: {local_video_path}")
                                        break  # 成功下载，跳出重试循环
                                    except Exception as e:
                                        retry_count += 1
                                        logger.warning(f"下载视频失败 (尝试 {retry_count}/{max_retries}): {e}")
                                        if retry_count >= max_retries:
                                            raise e  # 达到最大重试次数，抛出异常
                                        time.sleep(2)  # 等待2秒后重试
                                        
                                # 添加视频生成记录到数据库
                                try:
                                    # 获取使用的账号ID
                                    if account_id:
                                        # 添加视频生成记录
                                        add_record(account_id, 2)  # 2代表视频
                                        logger.info(f"视频生成记录已添加，账号ID: {account_id}")
                                    else:
                                        logger.warning("无法获取账号ID，跳过记录添加")
                                except Exception as e:
                                    logger.error(f"添加视频生成记录失败: {e}")
                                
                                return {'success': True, 'video_path': local_video_path, 'message': '视频生成成功'}
                            except Exception as e:
                                logger.error(f"下载视频失败: {e}")
                                return {'success': False, 'error': str(e)}
                        else:
                            # 添加视频生成记录到数据库
                            try:
                                # 获取使用的账号ID
                                if account_id:
                                    # 添加视频生成记录
                                    add_record(account_id, 2)  # 2代表视频
                                    logger.info(f"视频生成记录已添加，账号ID: {account_id}")
                                else:
                                    logger.warning("无法获取账号ID，跳过记录添加")
                            except Exception as e:
                                logger.error(f"添加视频生成记录失败: {e}")
                            
                            return {'success': True, 'message': '视频生成成功，但未获取到视频URL'}
                    else:
                        error_msg = result.get('error', '未知错误')
                        logger.error(f"视频生成失败: {error_msg}")
                        return {'success': False, 'error': error_msg}
                except Exception as e:
                    logger.error(f"调用视频生成函数失败: {e}")
                    return {'success': False, 'error': str(e)}
            else:
                # 如果没有图片路径，则使用文生视频作为备选
                logger.info(f"未提供图片路径，使用文生视频，提示词: {prompt}，时长: {video_duration}秒")
                # 移除对client的使用，直接返回错误信息
                logger.error("视频生成功能暂时不可用")
                return {'success': False, 'error': '视频生成功能暂时不可用'}
        except Exception as e:
            logger.error(f"生成视频失败: {e}")
            return {'success': False, 'error': str(e)}

    def batch_generate_images(self, files, prompt):
        """批量生成图片"""
        try:
            logger.info(f"开始批量生成图片，文件数量: {len(files)}, 提示词: {prompt}")
            
            # 用于跟踪生成结果
            success_count = 0
            failed_count = 0
            
            # 为每个文件生成图片
            for index, file in enumerate(files):
                main_image = None
                try:
                    main_image = file.get('main_image') if file else None
                    if not main_image:
                        logger.warning(f"文件缺少主图信息: {file}")
                        failed_count += 1
                        continue
                    
                    # 获取文件的unique_id，如果没有则生成一个
                    unique_id = file.get('uniqueId')
                    if not unique_id:
                        import uuid
                        unique_id = str(uuid.uuid4())
                        # 更新文件的unique_id
                        file['uniqueId'] = unique_id
                    
                    # 获取可用的图片账号
                    account_info = get_image_account()
                    logger.info(f"使用图片账号生成图片，账号ID: {account_info.get('id') if account_info else 'None'}")
                    
                    # 检查是否有可用账号
                    if not account_info:
                        error_msg = "没有可用的账号或均已达到使用上限"
                        logger.error(error_msg)
                        failed_count += 1
                        continue
                    
                    # 从账号信息中提取认证信息
                    username = account_info.get('username')
                    password = account_info.get('password')
                    cookies = account_info.get('cookies')
                    account_id = account_info.get('id')  # 获取账号ID
                    
                    # 调用 jimeng_image_util.py 中的图片生成函数
                    import asyncio
                    from jimeng_image_util import generate_image as jimeng_generate_image
                    
                    # 使用全局的 handless 变量控制是否使用无头模式
                    global handless
                    
                    # 使用 asyncio.run() 运行异步函数
                    try:
                        # 注意：这里需要在新的事件循环中运行，因为我们在同步函数中调用异步函数
                        result = asyncio.run(jimeng_generate_image(
                            cookies=cookies,
                            username=username,
                            password=password,
                            prompt=prompt,
                            image_path=main_image,
                            headless=not handless,  # 如果 handless 为 False，则 headless 参数为 True（无头模式）
                            account_id=account_id  # 传递账号ID用于保存cookies
                        ))
                        
                        # 处理生成结果
                        if result.get('success'):
                            logger.info(f"图片生成成功: {result}")
                            # 提取生成的图片URL并下载到本地
                            image_urls = result.get('image_urls', [])
                            local_image_paths = []
                            
                            if image_urls:
                                import os
                                import requests
                                from datetime import datetime
                                
                                # 创建保存图片的目录
                                app_dir = os.path.dirname(os.path.dirname(__file__))
                                save_dir = os.path.join(app_dir, "generated_images", datetime.now().strftime("%Y%m%d_%H%M%S"))
                                os.makedirs(save_dir, exist_ok=True)
                                logger.info(f"[DEBUG] Created save directory: {save_dir}")
                                
                                for i, image_url in enumerate(image_urls):
                                    try:
                                        # 下载图片（带重试逻辑）
                                        max_retries = 10  # 重试次数
                                        retry_count = 0
                                        
                                        while retry_count < max_retries:
                                            try:
                                                response = requests.get(image_url, timeout=30)
                                                response.raise_for_status()
                                                
                                                # 生成本地文件名
                                                file_extension = ".png"  # 默认扩展名
                                                if 'content-type' in response.headers:
                                                    content_type = response.headers['content-type']
                                                    if 'jpeg' in content_type or 'jpg' in content_type:
                                                        file_extension = ".jpg"
                                                    elif 'png' in content_type:
                                                        file_extension = ".png"
                                                    elif 'webp' in content_type:
                                                        file_extension = ".webp"
                                                
                                                local_filename = f"generated_image_{i+1}{file_extension}"
                                                local_filepath = os.path.join(save_dir, local_filename)
                                                
                                                # 保存图片到本地
                                                with open(local_filepath, 'wb') as f:
                                                    f.write(response.content)
                                                
                                                # 保存本地路径
                                                local_image_paths.append(local_filepath)
                                                logger.info(f"图片已保存到: {local_filepath}")
                                                break  # 成功下载，跳出重试循环
                                            except Exception as e:
                                                retry_count += 1
                                                logger.warning(f"下载图片失败 (尝试 {retry_count}/{max_retries}): {e}")
                                                if retry_count >= max_retries:
                                                    raise e  # 达到最大重试次数，抛出异常
                                                time.sleep(2)  # 等待2秒后重试
                                    except Exception as e:
                                        logger.error(f"下载图片失败: {e}")
                                        # 如果下载失败，仍然添加URL
                                        local_image_paths.append(image_url)
                            
                            # 添加图片生成记录到数据库
                            try:
                                # 获取使用的账号ID
                                if account_id:
                                    # 添加图片生成记录
                                    add_record(account_id, 1)  # 1代表图片
                                    logger.info(f"图片生成记录已添加，账号ID: {account_id}")
                                else:
                                    logger.warning("无法获取账号ID，跳过记录添加")
                            except Exception as e:
                                logger.error(f"添加图片生成记录失败: {e}")
                            
                            # 将本地图片路径传递给前端，并指定对应的item索引和唯一标识符
                            if self.window:
                                # 保存生成的图片路径到全局字典
                                for path in local_image_paths:
                                    self.add_generated_image(unique_id, path)
                                
                                # 转义路径中的特殊字符
                                escaped_paths = [path.replace('"', '\\"') for path in local_image_paths]
                                paths_js_array = str(escaped_paths)
                                # 传递当前生成索引和唯一标识符给前端
                                logger.info(f"[DEBUG] Calling frontend handleGeneratedImagesForItem with paths={paths_js_array}, index={index}, unique_id={unique_id}")
                                self.window.evaluate_js(f"handleGeneratedImagesForItem({paths_js_array}, {index}, '{unique_id}')")
                            
                            success_count += 1
                        else:
                            error_msg = result.get('error', '未知错误')
                            logger.error(f"图片生成失败: {error_msg}")
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"调用图片生成函数失败: {e}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"为文件生成图片失败: {main_image or '未知文件'}, 错误: {e}")
                    failed_count += 1
            
            logger.info(f"批量图片生成完成: 成功 {success_count} 个，失败 {failed_count} 个")
            return {'success': True, 'success_count': success_count, 'failed_count': failed_count}
        except Exception as e:
            logger.error(f"批量生成图片失败: {e}")
            return {'success': False, 'error': str(e)}

    def batch_generate_videos(self, files, prompt):
        """批量生成视频"""
        try:
            # 获取视频时长配置
            video_duration = get_config('video_duration', '5')  # 默认5秒
            logger.info(f"视频时长配置: {video_duration}秒")
            
            # 移除视频生成方式配置，只使用图生视频
            # 移除是否使用国内账号的配置，只使用国际账号
            
            # 将秒转换为毫秒
            duration_ms = int(video_duration) * 1000
            
            # 获取可用账号（用于视频生成）
            account_info = get_video_account()
            logger.info("使用视频账号批量生成视频")
            
            # 检查是否有可用账号
            if not account_info:
                error_msg = "没有可用的账号或均已达到使用上限"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            # 从账号信息中提取认证信息（优先使用cookies）
            auth_info = account_info.get('cookies')
            
            # 确保认证信息存在
            if not auth_info:
                logger.error("获取账号认证信息失败")
                return {'success': False, 'error': '获取账号认证信息失败'}
            # 移除jimeng_sdk的引用，直接使用None
            client = None

            # 图生视频模式，为每个文件生成视频
            success_count = 0
            failed_count = 0
            
            for index, file in enumerate(files):
                main_image = None
                try:
                    main_image = file.get('main_image')
                    if not main_image:
                        logger.warning(f"文件缺少主图信息: {file}")
                        failed_count += 1
                        continue
                    
                    # 生成一个唯一的ID用于此次调用
                    import uuid
                    unique_id = str(uuid.uuid4())
                    
                    # 从账号信息中提取认证信息
                    username = account_info.get('username')
                    password = account_info.get('password')
                    cookies = account_info.get('cookies')
                    account_id = account_info.get('id')  # 获取账号ID

                    # 生成视频
                    logger.info(f"开始为文件生成图生视频: {main_image}，提示词: {prompt}，时长: {video_duration}秒")
                    # 调用 jimeng_video_util.py 中的视频生成函数
                    import asyncio
                    from jimeng_video_util import generate_video as jimeng_generate_video
                    
                    # 使用全局的 handless 变量控制是否使用无头模式
                    global handless
                    
                    # 使用 asyncio.run() 运行异步函数
                    try:
                        # 注意：这里需要在新的事件循环中运行，因为我们在同步函数中调用异步函数
                        result = asyncio.run(jimeng_generate_video(
                            cookies=cookies,
                            username=username,
                            password=password,
                            prompt=prompt,
                            seconds=int(video_duration),
                            image_path=main_image,
                            headless=not handless,  # 如果 handless 为 False，则 headless 参数为 True（无头模式）
                            account_id=account_id  # 传递账号ID用于保存cookies
                        ))
                        
                        # 处理生成结果
                        if result.get('success'):
                            logger.info(f"视频生成成功: {result}")
                            # 提取生成的视频URL并下载到本地
                            video_url = result.get('video_url')
                            local_video_path = None
                            
                            if video_url:
                                try:
                                    import os
                                    import requests
                                    from datetime import datetime
                                    
                                    # 创建保存视频的目录
                                    app_dir = os.path.dirname(os.path.dirname(__file__))
                                    save_dir = os.path.join(app_dir, "generated_videos", datetime.now().strftime("%Y%m%d_%H%M%S"))
                                    os.makedirs(save_dir, exist_ok=True)
                                    logger.info(f"[DEBUG] Created save directory: {save_dir}")
                                    
                                    # 下载视频（带重试逻辑）
                                    max_retries = 10  # 重试次数
                                    retry_count = 0
                                    
                                    while retry_count < max_retries:
                                        try:
                                            response = requests.get(video_url, timeout=30)
                                            response.raise_for_status()
                                            
                                            # 生成本地文件名
                                            file_extension = ".mp4"  # 默认扩展名
                                            if 'content-type' in response.headers:
                                                content_type = response.headers['content-type']
                                                if 'mp4' in content_type:
                                                    file_extension = ".mp4"
                                                elif 'mov' in content_type:
                                                    file_extension = ".mov"
                                                elif 'avi' in content_type:
                                                    file_extension = ".avi"
                                            
                                            local_filename = f"generated_video{file_extension}"
                                            local_video_path = os.path.join(save_dir, local_filename)
                                            
                                            # 保存视频到本地
                                            with open(local_video_path, 'wb') as f:
                                                f.write(response.content)
                                            
                                            logger.info(f"视频已保存到: {local_video_path}")
                                            break  # 成功下载，跳出重试循环
                                        except Exception as e:
                                            retry_count += 1
                                            logger.warning(f"下载视频失败 (尝试 {retry_count}/{max_retries}): {e}")
                                            if retry_count >= max_retries:
                                                raise e  # 达到最大重试次数，抛出异常
                                            time.sleep(2)  # 等待2秒后重试
                                            
                                    # 添加视频生成记录到数据库
                                    try:
                                        # 获取使用的账号ID
                                        if account_id:
                                            # 添加视频生成记录
                                            add_record(account_id, 2)  # 2代表视频
                                            logger.info(f"视频生成记录已添加，账号ID: {account_id}")
                                        else:
                                            logger.warning("无法获取账号ID，跳过记录添加")
                                    except Exception as e:
                                        logger.error(f"添加视频生成记录失败: {e}")
                                    
                                    # 保存生成的视频路径到全局字典
                                    if local_video_path:
                                        self.add_generated_video(unique_id, local_video_path)
                                    
                                    success_count += 1
                                except Exception as e:
                                    logger.error(f"下载视频失败: {e}")
                                    failed_count += 1
                            else:
                                # 添加视频生成记录到数据库
                                try:
                                    # 获取使用的账号ID
                                    if account_id:
                                        # 添加视频生成记录
                                        add_record(account_id, 2)  # 2代表视频
                                        logger.info(f"视频生成记录已添加，账号ID: {account_id}")
                                    else:
                                        logger.warning("无法获取账号ID，跳过记录添加")
                                except Exception as e:
                                    logger.error(f"添加视频生成记录失败: {e}")
                                
                                success_count += 1
                        else:
                            error_msg = result.get('error', '未知错误')
                            logger.error(f"视频生成失败: {error_msg}")
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"调用视频生成函数失败: {e}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"为文件生成视频失败: {main_image}, 错误: {e}")
                    failed_count += 1
            
            logger.info(f"批量视频生成完成: 成功 {success_count} 个，失败 {failed_count} 个")
            return {'success': True, 'success_count': success_count, 'failed_count': failed_count}
        except Exception as e:
            logger.error(f"批量生成视频失败: {e}")
            return {'success': False, 'error': str(e)}

    def delete_item(self, main_image_path):
        """删除项目"""
        try:
            import os
            import shutil
            
            # 删除主图文件
            if os.path.exists(main_image_path):
                os.remove(main_image_path)
                logger.info(f"已删除主图文件: {main_image_path}")
            
            # 删除对应的子文件夹（如果存在）
            folder_path = os.path.dirname(main_image_path)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                shutil.rmtree(folder_path)
                logger.info(f"已删除文件夹: {folder_path}")
            
            return {'success': True}
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return {'success': False, 'error': str(e)}

    def debug_folder_structure(self, folder_path):
        """调试文件夹结构"""
        import os
        import glob
        
        logger.info(f"=== 调试文件夹结构: {folder_path} ===")
        
        # 验证文件夹路径
        if not os.path.exists(folder_path):
            logger.error(f"文件夹路径不存在: {folder_path}")
            return
        
        if not os.path.isdir(folder_path):
            logger.error(f"路径不是文件夹: {folder_path}")
            return
        
        # 列出所有文件
        try:
            all_items = os.listdir(folder_path)
            logger.info(f"文件夹中的所有项目数量: {len(all_items)}")
            
            # 分类文件和文件夹
            files = []
            dirs = []
            for item in all_items:
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    files.append(item)
                elif os.path.isdir(item_path):
                    dirs.append(item)
            
            logger.info(f"文件数量: {len(files)}, 文件夹数量: {len(dirs)}")
            logger.info(f"前10个文件: {files[:10]}")
            logger.info(f"所有文件夹: {dirs}")
            
            # 查找 images 和 items 文件夹
            images_folder = os.path.join(folder_path, "images")
            items_folder = os.path.join(folder_path, "items")
            
            logger.info(f"images文件夹路径: {images_folder}")
            logger.info(f"items文件夹路径: {items_folder}")
            
            if not os.path.exists(images_folder):
                logger.error(f"未找到 images 文件夹: {images_folder}")
            else:
                logger.info(f"找到 images 文件夹: {images_folder}")
                
                # 列出 images 文件夹中的子文件夹
                try:
                    image_subdirs = os.listdir(images_folder)
                    logger.info(f"images文件夹中的子文件夹数量: {len(image_subdirs)}")
                    logger.info(f"images文件夹中的子文件夹: {image_subdirs}")
                    
                    # 检查前几个子文件夹中的图片文件
                    for subdir in image_subdirs[:3]:  # 只检查前3个子文件夹
                        subdir_path = os.path.join(images_folder, subdir)
                        if os.path.isdir(subdir_path):
                            # 查找该子文件夹中的所有图片文件
                            image_files = []
                            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']:
                                pattern = os.path.join(subdir_path, ext)
                                image_files.extend(glob.glob(pattern))
                            
                            logger.info(f"子文件夹 {subdir} 中的图片文件数量: {len(image_files)}")
                            logger.info(f"子文件夹 {subdir} 中的前5个图片文件: {image_files[:5]}")
                except Exception as e:
                    logger.error(f"遍历 images 文件夹时出错: {e}")
            
            if not os.path.exists(items_folder):
                logger.error(f"未找到 items 文件夹: {items_folder}")
            else:
                logger.info(f"找到 items 文件夹: {items_folder}")
                
                # 列出 items 文件夹中的文件
                try:
                    item_files = os.listdir(items_folder)
                    logger.info(f"items文件夹中的文件数量: {len(item_files)}")
                    logger.info(f"items文件夹中的前10个文件: {item_files[:10]}")
                except Exception as e:
                    logger.error(f"遍历 items 文件夹时出错: {e}")
                
            # 查找图片文件
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']
            all_images = []
            for ext in image_extensions:
                pattern = os.path.join(folder_path, ext)
                images = glob.glob(pattern)
                all_images.extend(images)
                if images:
                    logger.info(f"找到 {ext} 文件: {len(images)} 个")
            
            logger.info(f"根目录下总共找到图片文件: {len(all_images)} 个")
            for img in all_images[:5]:  # 只显示前5个
                logger.info(f"  图片文件: {os.path.basename(img)}")
                
        except Exception as e:
            logger.error(f"调试文件夹结构时出错: {e}")

    def add_generated_image(self, unique_id, image_path):
        """添加生成的图片到指定unique_id的列表中"""
        logger.info(f"添加生成图片，unique_id: {unique_id}, image_path: {image_path}")
        if unique_id not in generated_images_dict:
            generated_images_dict[unique_id] = []
        generated_images_dict[unique_id].append(image_path)
        return {'success': True}

    def add_generated_video(self, unique_id, video_path):
        """添加生成的视频到指定unique_id的列表中"""
        logger.info(f"添加生成视频，unique_id: {unique_id}, video_path: {video_path}")
        # 使用一个全局字典来存储生成的视频
        global generated_videos_dict
        if 'generated_videos_dict' not in globals():
            generated_videos_dict = {}
        if unique_id not in generated_videos_dict:
            generated_videos_dict[unique_id] = []
        generated_videos_dict[unique_id].append(video_path)
        return {'success': True}

    def clear_generated_images(self, unique_id):
        """清空指定unique_id的生成图片列表"""
        logger.info(f"清空生成图片列表，unique_id: {unique_id}")
        if unique_id in generated_images_dict:
            generated_images_dict[unique_id] = []
        return {'success': True}

    def play_video(self, video_path):
        """使用系统默认播放器播放视频"""
        try:
            import os
            import platform
            import subprocess
            
            # 检查视频文件是否存在
            if not os.path.exists(video_path):
                return {'success': False, 'error': '视频文件不存在'}
            
            # 根据操作系统选择播放器
            system = platform.system()
            if system == "Windows":
                # Windows系统
                os.startfile(video_path)
            elif system == "Darwin":
                # macOS系统
                subprocess.call(["open", video_path])
            else:
                # Linux系统
                subprocess.call(["xdg-open", video_path])
            
            logger.info(f"视频播放成功: {video_path}")
            return {'success': True}
        except Exception as e:
            logger.error(f"播放视频失败: {e}")
            return {'success': False, 'error': str(e)}

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
    global thread_pool
    
    # 初始化数据库
    if not init_database():
        logger.error("数据库初始化失败，程序退出")
        sys.exit(1)
    
    # 从数据库配置中获取线程池大小
    max_threads_str = get_config('max_threads', '5')
    try:
        max_threads = int(max_threads_str)
    except (ValueError, TypeError):
        max_threads = 5
        logger.warning(f"无法解析线程池大小配置，使用默认值: {max_threads}")
    
    # 创建线程池
    thread_pool = ThreadPoolExecutor(max_workers=max_threads)
    logger.info(f"线程池已创建，最大线程数: {max_threads}")

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

    # 使用默认的较大窗口尺寸
    window = webview.create_window(
        title='Jimeng Scripts',
        url=f'file://{html_file}',
        js_api=api,
        width=1920,  # 默认宽度
        height=1080,  # 默认高度
        resizable=True,
        background_color='#ffffff'
    )

    # 将窗口对象传递给API
    api.set_window(window)

    try:
        # 启动应用，关闭调试模式
        webview.start()
    finally:
        # 关闭数据库连接
        close_database()
        # 关闭线程池
        if thread_pool:
            thread_pool.shutdown(wait=True)
            logger.info("线程池已关闭")
        logger.info("应用关闭")


if __name__ == '__main__':
    main()