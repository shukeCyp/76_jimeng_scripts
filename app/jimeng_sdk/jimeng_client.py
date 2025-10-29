#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
即梦AI Python SDK 客户端
提供简洁的 API 接口封装
"""

import sys
import os
from typing import Dict, Any, Optional, List, Union

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .core.core import get_credit, token_split, receive_credit
from .core.images import generate_images, generate_image_composition
from .core.videos import generate_video

class JimengClient:
    """即梦AI客户端类"""
    
    def __init__(self, token: str):
        """
        初始化即梦AI客户端
        
        Args:
            token (str): 认证令牌
        """
        self.token = token
        self.tokens = token_split(f"Bearer {token}")
    
    def get_credit(self) -> Dict[str, Any]:
        """
        获取积分信息
        
        Returns:
            Dict[str, Any]: 积分信息字典
                - giftCredit: 赠送积分
                - purchaseCredit: 购买积分
                - vipCredit: VIP积分
                - totalCredit: 总积分
        """
        return get_credit(self.token)
    
    def receive_credit(self) -> Dict[str, Any]:
        """
        接收今日积分
        
        Returns:
            Dict[str, Any]: 积分接收结果
                - cur_total_credits: 当前总积分
                - receive_quota: 本次接收的积分数
        """
        # 先获取当前积分信息
        current_credit = self.get_credit()
        current_total = current_credit["totalCredit"]
        
        # 接收积分
        new_total = receive_credit(self.token)
        
        # 计算接收的积分数
        received_quota = new_total - current_total if new_total > current_total else 0
        
        return {
            "cur_total_credits": new_total,
            "receive_quota": received_quota
        }
    
    def generate_images(
        self,
        prompt: str,
        model: str = "jimeng-4.0",
        options: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        生成图像
        
        Args:
            prompt (str): 图像生成提示词
            model (str): 模型名称，默认为 "jimeng-4.0"
            options (Dict[str, Any], optional): 其他选项参数
                - ratio (str): 图像比例，默认为 "1:1"
                - resolution (str): 分辨率，默认为 "2k"
                - sampleStrength (float): 采样强度，默认为 0.5
                - negativePrompt (str): 负面提示词，默认为空字符串
            
        Returns:
            List[str]: 生成的图像URL列表
            
        Example:
            client = JimengClient("your_token")
            images = client.generate_images("一只可爱的猫咪", "jimeng-4.0", {
                "ratio": "1:1",
                "resolution": "2k"
            })
        """
        if options is None:
            options = {}
        return generate_images(model, prompt, options, refresh_token=self.token)
    
    def generate_image_composition(
        self,
        prompt: str,
        images: List[Union[str, bytes]],
        model: str = "jimeng-4.0",
        options: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        图像合成（图生图）
        
        Args:
            prompt (str): 图像合成提示词
            images (List[Union[str, bytes]]): 输入图像列表，可以是URL字符串或bytes数据
            model (str): 模型名称，默认为 "jimeng-4.0"
            options (Dict[str, Any], optional): 其他选项参数
                - ratio (str): 图像比例，默认为 "1:1"
                - resolution (str): 分辨率，默认为 "2k"
                - sampleStrength (float): 采样强度，默认为 0.5
                - negativePrompt (str): 负面提示词，默认为空字符串
            
        Returns:
            List[str]: 生成的图像URL列表
            
        Example:
            # 使用本地图片文件
            with open("image.png", "rb") as f:
                image_data = f.read()
            images = client.generate_image_composition("将这张图片转换为油画风格", [image_data], "jimeng-4.0")
            
            # 使用图片URL
            images = client.generate_image_composition("将这张图片转换为油画风格", 
                ["https://example.com/image.jpg"], "jimeng-4.0")
        """
        if options is None:
            options = {}
        return generate_image_composition(model, prompt, images, options, self.token)
    
    def generate_video(
        self,
        prompt: str,
        model: str = "jimeng-video-3.0",
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成视频（图生视频）
        
        Args:
            prompt (str): 视频生成提示词
            model (str): 模型名称，默认为 "jimeng-video-3.0"
            options (Dict[str, Any], optional): 其他选项参数
                - width (int): 视频宽度，默认为 1024
                - height (int): 视频高度，默认为 1024
                - resolution (str): 分辨率，默认为 "720p"
                - filePaths (List[str]): 图片文件路径列表
            
        Returns:
            str: 生成的视频URL
            
        Example:
            # 使用本地图片文件生成视频
            video_url = client.generate_video("基于这张图片生成一个动态视频", "jimeng-video-3.0", {
                "width": 512,
                "height": 512,
                "resolution": "480p",
                "filePaths": ["/path/to/image.png"]
            })
        """
        if options is None:
            options = {}
        return generate_video(model, prompt, options, self.token)