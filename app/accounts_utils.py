#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
账号工具类
提供账号筛选和管理功能
"""

from database import JimengAccount, JimengRecord, get_config
from datetime import datetime
import random
# 导入peewee的fn，用于日期函数
from peewee import fn
from typing import Optional, Dict, Any
import json


def get_available_account(type: int) -> Optional[JimengAccount]:
    """
    获取可用账号
    type = 1 代表图片
    type = 2 代表视频
    :return: 可用账号列表
    """
    # 获取配置并确保是整数类型
    daily_video_limit = get_config("daily_video_limit", "2")
    daily_image_limit = get_config("daily_image_limit", "10")
    
    # 确保配置值是整数类型
    try:
        daily_video_limit = int(daily_video_limit)
    except (ValueError, TypeError):
        daily_video_limit = 2  # 默认值
        
    try:
        daily_image_limit = int(daily_image_limit)
    except (ValueError, TypeError):
        daily_image_limit = 10  # 默认值
    
    # 获取所有账号
    accounts = list(JimengAccount.select())
    
    # 获取今天的日期
    today = datetime.now().date()
    
    # 筛选可用账号
    available_accounts = []
    for account in accounts:
        # 查询该账号今天的生成记录数量
        if type == 1:  # 图片
            limit = daily_image_limit
        elif type == 2:  # 视频
            limit = daily_video_limit
        else:
            continue
        
        # 计算今天的生成记录数量
        today_records = JimengRecord.select().where(
            (JimengRecord.account == account) & 
            (JimengRecord.type == type) &
            (fn.date(JimengRecord.time) == today)
        ).count()
        
        # 如果未超过限制，则为可用账号
        # 确保比较的是相同类型
        if int(today_records) < int(limit):
            available_accounts.append(account)
    
    # 随机返回一个可用账号
    if available_accounts:
        return random.choice(available_accounts)
    
    return None


def get_image_account() -> Optional[Dict[str, Any]]:
    """
    获取图片类型的可用账号
    :return: 可用账号信息字典
    """
    account = get_available_account(1)  # 1代表图片类型
    if account:
        # 解析cookies字符串为列表
        cookies = None
        if account.cookies:
            try:
                cookies = json.loads(str(account.cookies))
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，保持为None
                pass
        
        return {
            'id': account.get_id(),  # 使用 get_id() 方法获取主键
            'username': account.username,
            'password': account.password,
            'cookies': cookies
        }
    return None


def get_video_account() -> Optional[Dict[str, Any]]:
    """
    获取视频类型的可用账号
    :return: 可用账号信息字典
    """
    account = get_available_account(2)  # 2代表视频类型
    if account:
        # 解析cookies字符串为列表
        cookies = None
        if account.cookies:
            try:
                cookies = json.loads(str(account.cookies))
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，保持为None
                pass
        
        return {
            'id': account.get_id(),  # 使用 get_id() 方法获取主键
            'username': account.username,
            'password': account.password,
            'cookies': cookies
        }
    return None


def update_account_cookies(account_id: int, cookies: list) -> bool:
    """
    更新账号的cookies
    :param account_id: 账号ID
    :param cookies: cookies列表
    :return: 更新是否成功
    """
    try:
        # 将cookies列表转换为JSON字符串存储
        cookies_str = json.dumps(cookies)
        
        # 更新账号的cookies字段
        query = JimengAccount.update(cookies=cookies_str).where(JimengAccount.id == account_id)
        updated_rows = query.execute()
        
        if updated_rows > 0:
            print(f"账号 {account_id} 的cookies已更新")
            return True
        else:
            print(f"未找到账号 {account_id}")
            return False
    except Exception as e:
        print(f"更新账号cookies失败: {e}")
        return False