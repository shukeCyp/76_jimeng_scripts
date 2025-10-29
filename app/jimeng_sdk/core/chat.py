import os
import sys
import json
import time
from typing import Any, Dict, List
# 移除Flask导入，使用简单的Response类
# from flask import Response, stream_with_context

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..lib.logger import logger
from ..lib.util import uuid_generator, unix_timestamp
from ..lib.exceptions.api_exception import APIException
from ..lib.consts.exceptions import EX
from .images import generate_images, generate_image_composition, DEFAULT_MODEL
from .videos import generate_video, DEFAULT_MODEL as DEFAULT_VIDEO_MODEL

# 创建简单的Response类来替代Flask的Response
class Response:
    def __init__(self, response=None, status=None, headers=None, mimetype=None):
        self.response = response
        self.status = status
        self.headers = headers or {}
        self.mimetype = mimetype

# 默认模型
DEFAULT_CHAT_MODEL = DEFAULT_MODEL

def parse_model(model: str) -> Dict[str, Any]:
    """解析模型"""
    parts = model.split(":")
    _model = parts[0]
    
    width = 1024
    height = 1024
    
    if len(parts) > 1:
        size_parts = parts[1].split("x")
        if len(size_parts) == 2:
            try:
                width = int(size_parts[0])
                height = int(size_parts[1])
                # 确保宽高是偶数
                width = (width + 1) // 2 * 2
                height = (height + 1) // 2 * 2
            except ValueError:
                pass
    
    return {
        "model": _model,
        "width": width,
        "height": height,
    }

def is_video_model(model: str) -> bool:
    """检测是否为视频生成请求"""
    return model.startswith("jimeng-video")

def create_completion(
    messages: List[Dict[str, Any]],
    refresh_token: str,
    _model: str = DEFAULT_CHAT_MODEL,
    retry_count: int = 0
) -> Dict[str, Any]:
    """同步对话补全"""
    try:
        if len(messages) == 0:
            raise APIException(EX.API_REQUEST_PARAMS_INVALID, "消息不能为空")

        model_info = parse_model(_model)
        model_name = model_info["model"]
        width = model_info["width"]
        height = model_info["height"]
        
        logger.info(f"Messages: {json.dumps(messages, ensure_ascii=False)}")
        logger.info(f"Model info: model={model_name}, width={width}, height={height}")

        # 检查是否为视频生成请求
        if is_video_model(_model):
            try:
                # 视频生成
                logger.info(f"开始生成视频，模型: {_model}")
                
                video_url = generate_video(
                    _model,
                    messages[-1]["content"],
                    {
                        "width": width,
                        "height": height,
                        "resolution": "720p",  # 默认分辨率
                    },
                    refresh_token
                )

                logger.info(f"视频生成成功，URL: {video_url}")
                return {
                    "id": uuid_generator(),
                    "model": _model,
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": f"![video]({video_url})\n",
                            },
                            "finish_reason": "stop",
                        },
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "created": unix_timestamp(),
                }
            except APIException:
                raise
            except Exception as e:
                logger.error(f"视频生成失败: {str(e)}")
                return {
                    "id": uuid_generator(),
                    "model": _model,
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": f"生成视频失败: {str(e)}\n\n如果您在即梦官网看到已生成的视频，可能是获取结果时出现了问题，请前往即梦官网查看。",
                            },
                            "finish_reason": "stop",
                        },
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "created": unix_timestamp(),
                }
        else:
            # 图像生成
            logger.info(f"开始生成图像，模型: {model_name}, 提示词: {messages[-1]['content']}")
            image_urls = generate_images(
                model_name,
                messages[-1]["content"],
                {
                    "width": width,
                    "height": height,
                },
                refresh_token
            )
            logger.info(f"图像生成完成，URLs: {image_urls}")

            return {
                "id": uuid_generator(),
                "model": _model or model_name,
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "".join([f"![image_{i}]({url})\n" for i, url in enumerate(image_urls)]),
                        },
                        "finish_reason": "stop",
                    },
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "created": unix_timestamp(),
            }
    except Exception as e:
        logger.error(f"Response error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        if retry_count < 3:  # 最多重试3次
            logger.warn(f"Try again after 2s...")
            time.sleep(2)
            return create_completion(messages, refresh_token, _model, retry_count + 1)
        raise e

def create_completion_stream(
    messages: List[Dict[str, Any]],
    refresh_token: str,
    _model: str = DEFAULT_CHAT_MODEL,
    retry_count: int = 0
) -> Response:
    """流式对话补全"""
    
    def generate():
        try:
            model_info = parse_model(_model)
            model_name = model_info["model"]
            width = model_info["width"]
            height = model_info["height"]
            
            logger.info(f"Messages: {json.dumps(messages, ensure_ascii=False)}")

            if len(messages) == 0:
                logger.warn("消息为空，返回空流")
                yield "data: [DONE]\n\n"
                return

            # 检查是否为视频生成请求
            if is_video_model(_model):
                # 视频生成
                yield "data: " + json.dumps({
                    "id": uuid_generator(),
                    "model": _model,
                    "object": "chat.completion.chunk",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": "🎬 视频生成中，请稍候...\n这可能需要1-2分钟，请耐心等待"},
                            "finish_reason": None,
                        },
                    ],
                }) + "\n\n"

                # 发送进度点
                for i in range(24):  # 模拟2分钟的进度
                    time.sleep(5)
                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": "."},
                                "finish_reason": None,
                            },
                        ],
                    }) + "\n\n"

                try:
                    logger.info(f"开始生成视频，模型: {_model}, 提示词: {messages[-1]['content'][:50]}...")
                    
                    # 先给用户一个初始提示
                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "role": "assistant",
                                    "content": "\n\n🎬 视频生成已开始，这可能需要几分钟时间...",
                                },
                                "finish_reason": None,
                            },
                        ],
                    }) + "\n\n"

                    video_url = generate_video(
                        _model,
                        messages[-1]["content"],
                        {"width": width, "height": height, "resolution": "720p"},
                        refresh_token
                    )

                    logger.info(f"视频生成成功，URL: {video_url}")

                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 1,
                                "delta": {
                                    "role": "assistant",
                                    "content": f"\n\n✅ 视频生成完成！\n\n![video]({video_url})\n\n您可以：\n1. 直接查看上方视频\n2. 使用以下链接下载或分享：{video_url}",
                                },
                                "finish_reason": None,
                            },
                        ],
                    }) + "\n\n"

                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 2,
                                "delta": {
                                    "role": "assistant",
                                    "content": "",
                                },
                                "finish_reason": "stop",
                            },
                        ],
                    }) + "\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as err:
                    logger.error(f"视频生成失败: {str(err)}")
                    logger.error(f"错误详情: {str(err)}")

                    # 构建更详细的错误信息
                    error_message = f"⚠️ 视频生成过程中遇到问题: {str(err)}"

                    # 如果是历史记录不存在的错误，提供更具体的建议
                    if "历史记录不存在" in str(err):
                        error_message += "\n\n可能原因：\n1. 视频生成请求已发送，但API无法获取历史记录\n2. 视频生成服务暂时不可用\n3. 历史记录ID无效或已过期\n\n建议操作：\n1. 请前往即梦官网查看您的视频是否已生成：https://jimeng.jianying.com/ai-tool/video/generate\n2. 如果官网已显示视频，但这里无法获取，可能是API连接问题\n3. 如果官网也没有显示，请稍后再试或重新生成视频"
                    elif "获取视频生成结果超时" in str(err):
                        error_message += "\n\n视频生成可能仍在进行中，但等待时间已超过系统设定的限制。\n\n请前往即梦官网查看您的视频：https://jimeng.jianying.com/ai-tool/video/generate\n\n如果您在官网上看到视频已生成，但这里无法显示，可能是因为：\n1. 获取结果的过程超时\n2. 网络连接问题\n3. API访问限制"
                    else:
                        error_message += "\n\n如果您在即梦官网看到已生成的视频，可能是获取结果时出现了问题。\n\n请访问即梦官网查看您的创作历史：https://jimeng.jianying.com/ai-tool/video/generate"

                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 1,
                                "delta": {
                                    "role": "assistant",
                                    "content": f"\n\n{error_message}",
                                },
                                "finish_reason": "stop",
                            },
                        ],
                    }) + "\n\n"
                    yield "data: [DONE]\n\n"
            else:
                # 图像生成
                yield "data: " + json.dumps({
                    "id": uuid_generator(),
                    "model": _model or model_name,
                    "object": "chat.completion.chunk",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": "🎨 图像生成中，请稍候..."},
                            "finish_reason": None,
                        },
                    ],
                }) + "\n\n"

                try:
                    image_urls = generate_images(
                        model_name,
                        messages[-1]["content"],
                        {"width": width, "height": height},
                        refresh_token
                    )

                    for i, url in enumerate(image_urls):
                        yield "data: " + json.dumps({
                            "id": uuid_generator(),
                            "model": _model or model_name,
                            "object": "chat.completion.chunk",
                            "choices": [
                                {
                                    "index": i + 1,
                                    "delta": {
                                        "role": "assistant",
                                        "content": f"![image_{i}]({url})\n",
                                    },
                                    "finish_reason": "stop" if i == len(image_urls) - 1 else None,
                                },
                            ],
                        }) + "\n\n"
                    
                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model or model_name,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": len(image_urls) + 1,
                                "delta": {
                                    "role": "assistant",
                                    "content": "图像生成完成！",
                                },
                                "finish_reason": "stop",
                            },
                        ],
                    }) + "\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as err:
                    yield "data: " + json.dumps({
                        "id": uuid_generator(),
                        "model": _model or model_name,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 1,
                                "delta": {
                                    "role": "assistant",
                                    "content": f"生成图片失败: {str(err)}",
                                },
                                "finish_reason": "stop",
                            },
                        ],
                    }) + "\n\n"
                    yield "data: [DONE]\n\n"
        except Exception as e:
            if retry_count < 3:  # 最多重试3次
                logger.error(f"Response error: {str(e)}")
                logger.warn(f"Try again after 2s...")
                time.sleep(2)
                # 重新生成流
                for chunk in generate():
                    yield chunk
            else:
                yield "data: " + json.dumps({
                    "id": uuid_generator(),
                    "model": _model,
                    "object": "chat.completion.chunk",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": f"请求处理失败: {str(e)}",
                            },
                            "finish_reason": "stop",
                        },
                    ],
                }) + "\n\n"
                yield "data: [DONE]\n\n"

    # 返回一个简单的Response对象而不是Flask Response
    return Response(generate(), mimetype='text/event-stream')