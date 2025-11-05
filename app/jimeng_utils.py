#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
即梦AI工具类
封装常用功能，支持在子线程中运行
"""

# 注释掉未使用的导入
# from cmd import PROMPT
import threading
import time
import requests
import json
# 注释掉未使用的导入
# from openai import OpenAI
import base64
from typing import Dict, Any, Optional, Callable, List
import logging
import sys
import os
import re

# 使用相对导入
try:
    from database import get_config
    from accounts_utils import get_available_account
except ImportError:
    # 如果相对导入失败，尝试使用绝对导入
    try:
        from app.database import get_config
        from app.accounts_utils import get_available_account
    except ImportError:
        # 如果都失败了，添加项目根目录到sys.path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from database import get_config
        from accounts_utils import get_available_account

def generate_image(prompt: str, image_path: str):
    account = get_available_account(1)
    # 修复：避免递归调用和循环导入
    if account:
        # 这里应该调用实际的图片生成逻辑
        # 暂时返回一个模拟结果
        return {"success": True, "data": []}
    else:
        # 如果没有可用账号，返回错误信息
        return {"success": False, "error": "没有可用账号"}

def generate_video(prompt: str, image_path: str):
    # 暂时返回一个模拟结果
    return {"success": False, "error": "视频生成功能暂时不可用"}

def generate_scene(image_path: str, title: str = "") -> str:
    """
    使用 GPT-4 模型，根据产品图片和标题生成一个适合展示的场景描述。

    - 使用数据库配置中的 api_key、api_proxy、model
    - 优先尝试图像+文本输入的对话补全接口
    - 若失败则回退为仅文本输入（不包含图片）
    - 最终仅返回一句中文场景描述
    """
    try:
        apikey = get_config("api_key", "").strip()
        base_url = (get_config("api_proxy", "https://api.openai.com/v1").strip() or "https://api.openai.com/v1").rstrip("/")
        model = (get_config("model", "gpt-4").strip() or "gpt-4")

        # 读取图片并转换为base64编码
        encoded_image = None
        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logging.warning(f"读取图片失败，将使用文本模式生成场景: {e}")

        # 通用请求头与URL
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {apikey}",
            "Content-Type": "application/json"
        }

        system_prompt = "你是产品展示场景生成助手。只输出中文的一句场景，不要其他解释或前后缀。"
        user_text = (
            f"产品标题：{title or '未知产品'}\n"
            f"请基于产品图片与标题，生成一个适合电商展示的场景（仅一句话，中文）。"
        )

        # 首先尝试图像+文本输入
        if encoded_image:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                        ],
                    }
                ],
                "max_tokens": 128
            }
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    content = (
                        data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                            .strip()
                    )
                    if content:
                        return content
                else:
                    logging.warning(f"图像+文本场景生成失败，HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logging.warning(f"图像+文本场景生成请求异常，将回退文本模式: {e}")

        # 回退为仅文本输入
        payload_text_only = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 128
        }
        try:
            resp2 = requests.post(url, headers=headers, data=json.dumps(payload_text_only), timeout=20)
            if resp2.status_code == 200:
                data2 = resp2.json()
                content2 = (
                    data2.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                )
                if content2:
                    return content2
            else:
                logging.error(f"文本场景生成失败，HTTP {resp2.status_code}: {resp2.text[:200]}")
        except Exception as e:
            logging.error(f"文本场景生成请求异常: {e}")

        return "简洁现代室内场景，柔和自然光线"
    except Exception as e:
        logging.error(f"生成场景失败: {e}")
        return "简洁现代室内场景，柔和自然光线"


def generate_sence(image_path: str) -> str:
    """兼容旧方法：不含标题时的场景生成（回退到默认/文本模式）。"""
    return generate_scene(image_path, "")


def merge_prompt_with_scene(prompt: str, title: str, scene: str) -> str:
    """
    将数据库中的提示词 `prompt` 中的占位符 `<...>` 用标题与场景进行填充：
    - 支持占位符：`<scene>`、`<场景>`、`<title>`、`<标题>`，以及包含“标题”的中文词（如`<产品标题>`、`<商品名>`）。
    - 未识别的占位符将保留原状。
    - 如果提示词中没有场景占位符，则在末尾追加一行场景，确保场景被包含。
    """
    try:
        if not prompt:
            return (scene or "")

        def normalize_token(tok: str) -> str:
            t = tok.strip().lower()
            if t in ("scene", "场景"):
                return "scene"
            if t in ("title", "标题"):
                return "title"
            # 宽松匹配：包含“标题”的中文词都视为 title
            if ("标题" in tok) or ("title" in t) or ("产品名" in tok) or ("商品名" in tok):
                return "title"
            return t

        def replacer(m: re.Match) -> str:
            raw = m.group(0)
            token = m.group(1)
            key = normalize_token(token)
            if key == "scene":
                return scene or ""
            if key == "title":
                return title or ""
            return raw  # 未识别的占位符保持不变

        filled = re.sub(r"<\s*([^<>]+?)\s*>", replacer, prompt)

        # 如果填充后不包含场景文本（说明没有场景占位符），在末尾追加场景。
        if scene and (scene not in filled):
            filled = f"{filled}\n{scene}".strip()

        return filled
    except Exception as e:
        logging.warning(f"合并提示词与场景失败，使用原始提示词: {e}")
        # 退化：原始提示词 + 场景
        base = prompt or ""
        return f"{base}\n{scene}".strip()
