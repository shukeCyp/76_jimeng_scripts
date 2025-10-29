#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
即梦AI简化版SDK
提供直接的函数调用接口，无需启动Web服务
"""

from .core.core import get_credit, token_split, receive_credit
from .core.images import generate_images, generate_image_composition
from .core.videos import generate_video
from .jimeng_client import JimengClient

__version__ = "1.0.0"
__author__ = "Jimeng AI"

__all__ = [
    "get_credit",
    "token_split",
    "receive_credit",
    "generate_images",
    "generate_image_composition",
    "generate_video",
    "JimengClient"
]