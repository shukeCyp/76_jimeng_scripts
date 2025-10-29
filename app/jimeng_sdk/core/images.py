import os
import sys
import uuid
import time
import hashlib
import requests
import json
import zlib
from typing import Any, Dict, List, Union

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..lib.logger import logger
from ..lib.exceptions.api_exception import APIException
from ..lib.consts.exceptions import EX
from ..lib.util import uuid_generator
from .core import request_api, get_credit, receive_credit

# 默认模型
DEFAULT_MODEL = "jimeng-4.0"
DEFAULT_IMAGE_MODEL = "jimeng-4.0"

# 模型映射（与TS保持一致）
IMAGE_MODEL_MAP = {
    "jimeng-4.0": "high_aes_general_v40",
    "jimeng-3.1": "high_aes_general_v30l_art_fangzhou:general_v3.0_18b",
    "jimeng-3.0": "high_aes_general_v30l:general_v3.0_18b",
    "jimeng-2.1": "high_aes_general_v21_L:general_v2.1_L",
    "jimeng-2.0-pro": "high_aes_general_v20_L:general_v2.0_L",
    "jimeng-2.0": "high_aes_general_v20:general_v2.0",
    "jimeng-1.4": "high_aes_general_v14:general_v1.4",
    "jimeng-xl-pro": "text2img_xl_sft"
}

# US地区模型映射
IMAGE_MODEL_MAP_US = {
    "jimeng-4.0": "high_aes_general_v40",
    "jimeng-3.0": "high_aes_general_v30l:general_v3.0_18b",
    "nanobanana": "external_model_gemini_flash_image_v25",
}

# 分辨率选项
RESOLUTION_OPTIONS = {
    "2k": {
        "1:1": {"width": 2048, "height": 2048, "ratio": 1},
        "4:3": {"width": 2304, "height": 1728, "ratio": 4},
        "3:4": {"width": 1728, "height": 2304, "ratio": 2},
        "16:9": {"width": 2560, "height": 1440, "ratio": 3},
        "9:16": {"width": 1440, "height": 2560, "ratio": 5},
        "3:2": {"width": 2496, "height": 1664, "ratio": 7},
        "2:3": {"width": 1664, "height": 2496, "ratio": 6},
        "21:9": {"width": 3024, "height": 1296, "ratio": 8},
    },
    "1k": {
        "1:1": {"width": 1328, "height": 1328, "ratio": 1},
        "4:3": {"width": 1472, "height": 1104, "ratio": 4},
        "3:4": {"width": 1104, "height": 1472, "ratio": 2},
        "16:9": {"width": 1664, "height": 936, "ratio": 3},
        "9:16": {"width": 936, "height": 1664, "ratio": 5},
        "3:2": {"width": 1584, "height": 1056, "ratio": 7},
        "2:3": {"width": 1056, "height": 1584, "ratio": 6},
        "21:9": {"width": 2016, "height": 864, "ratio": 8},
    },
    "4k": {
        "1:1": {"width": 4096, "height": 4096, "ratio": 101},
        "4:3": {"width": 4608, "height": 3456, "ratio": 104},
        "3:4": {"width": 3456, "height": 4608, "ratio": 102},
        "16:9": {"width": 5120, "height": 2880, "ratio": 103},
        "9:16": {"width": 2880, "height": 5120, "ratio": 105},
        "3:2": {"width": 4992, "height": 3328, "ratio": 107},
        "2:3": {"width": 3328, "height": 4992, "ratio": 106},
        "21:9": {"width": 6048, "height": 2592, "ratio": 108}
    }
}

# 常量
DRAFT_VERSION = "3.3.2"
DRAFT_MIN_VERSION = "3.0.5"
DEFAULT_ASSISTANT_ID_CN = 513695  # 数字类型
DEFAULT_ASSISTANT_ID_US = 513641  # US地区助手ID


def get_resolution_params(resolution: str = '2k', ratio: str = '1:1') -> Dict[str, Any]:
    """获取分辨率参数"""
    resolution_group = RESOLUTION_OPTIONS.get(resolution)
    if not resolution_group:
        supported_resolutions = ", ".join(RESOLUTION_OPTIONS.keys())
        raise Exception(f"不支持的分辨率 \"{resolution}\"。支持的分辨率: {supported_resolutions}")
    
    ratio_config = resolution_group.get(ratio)
    if not ratio_config:
        supported_ratios = ", ".join(resolution_group.keys())
        raise Exception(f"在 \"{resolution}\" 分辨率下，不支持的比例 \"{ratio}\"。支持的比例: {supported_ratios}")
    
    return {
        "width": ratio_config["width"],
        "height": ratio_config["height"],
        "image_ratio": ratio_config["ratio"],
        "resolution_type": resolution,
    }


def get_model(model: str, is_us: bool = False) -> str:
    """获取模型（与TS保持一致）"""
    model_map = IMAGE_MODEL_MAP_US if is_us else IMAGE_MODEL_MAP
    if is_us and model not in model_map:
        supported_models = ", ".join(model_map.keys())
        raise Exception(f"国际版不支持模型 \"{model}\"。支持的模型: {supported_models}")
    return model_map.get(model, model_map[DEFAULT_MODEL])


def calculate_crc32(data: bytes) -> str:
    """计算CRC32"""
    return format(zlib.crc32(data) & 0xffffffff, '08x')


def upload_image_from_url(image_url: str, refresh_token: str) -> str:
    """从URL上传图片"""
    try:
        logger.info(f"开始上传图片: {image_url}")
        
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content
        
        return upload_image_from_buffer(image_data, refresh_token)
    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        raise e


def upload_image_from_buffer(image_data: bytes, refresh_token: str) -> str:
    """从缓冲区上传图片"""
    try:
        logger.info("开始通过Buffer上传图片...")
        
        # 获取上传令牌
        token_result = request_api("post", "/mweb/v1/get_upload_token", refresh_token, {
            "data": {
                "scene": 2,
            },
            "params": {
                "aid": DEFAULT_ASSISTANT_ID_CN,
            },
            "noDefaultParams": True
        })
        
        # 从响应中提取令牌信息
        data = token_result.get("data", {})
        access_key_id = data.get("access_key_id") or token_result.get("access_key_id")
        secret_access_key = data.get("secret_access_key") or token_result.get("secret_access_key")
        session_token = data.get("session_token") or token_result.get("session_token")
        service_id = data.get("service_id") or token_result.get("service_id", "tb4s082cfz")
        
        if not access_key_id or not secret_access_key or not session_token:
            raise Exception("获取上传令牌失败")
        
        logger.info(f"获取上传令牌成功: service_id={service_id}")
        
        file_size = len(image_data)
        crc32 = calculate_crc32(image_data)
        
        logger.info(f"图片Buffer: 大小={file_size}字节, CRC32={crc32}")
        
        # 申请上传权限
        now = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        random_str = uuid_generator()[:10]
        apply_url_host = 'https://imagex.bytedanceapi.com'
        apply_url = f"{apply_url_host}/?Action=ApplyImageUpload&Version=2018-08-01&ServiceId={service_id}&FileSize={file_size}&s={random_str}"
        
        # 构建请求头
        request_headers = {
            'x-amz-date': now,
            'x-amz-security-token': session_token
        }
        
        # 实现AWS4-HMAC-SHA256签名算法
        def sign(key, msg):
            import hmac
            import hashlib
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        
        def create_signature(method, url, headers, access_key_id, secret_access_key, session_token=None, payload=''):
            import hmac
            import hashlib
            from urllib.parse import urlparse, parse_qs
            from datetime import datetime
            
            # 解析URL
            parsed_url = urlparse(url)
            pathname = parsed_url.path or '/'
            search = parsed_url.query
            
            # 创建规范请求
            timestamp = headers['x-amz-date']
            date = timestamp[:8]
            region = 'cn-north-1'
            service = 'imagex'
            
            # 规范化查询参数
            search_params = parse_qs(search)
            query_params = []
            for key in sorted(search_params.keys()):
                for value in sorted(search_params[key]):
                    query_params.append((key, value))
            
            canonical_query_string = '&'.join([f'{key}={value}' for key, value in query_params])
            
            # 规范化头部
            headers_to_sign = {
                'x-amz-date': timestamp
            }
            
            if session_token:
                headers_to_sign['x-amz-security-token'] = session_token
            
            payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest() if payload else hashlib.sha256(b'').hexdigest()
            if method.upper() == 'POST' and payload:
                headers_to_sign['x-amz-content-sha256'] = payload_hash
            
            signed_headers = ';'.join(sorted([k.lower() for k in headers_to_sign.keys()]))
            
            canonical_headers = '\n'.join([f'{k.lower()}:{v.strip()}' for k, v in sorted(headers_to_sign.items())]) + '\n'
            
            canonical_request = '\n'.join([
                method.upper(),
                pathname,
                canonical_query_string,
                canonical_headers,
                signed_headers,
                payload_hash
            ])
            
            # 创建待签名字符串
            credential_scope = f'{date}/{region}/{service}/aws4_request'
            string_to_sign = '\n'.join([
                'AWS4-HMAC-SHA256',
                timestamp,
                credential_scope,
                hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
            ])
            
            # 生成签名
            k_date = sign(('AWS4' + secret_access_key).encode('utf-8'), date)
            k_region = sign(k_date, region)
            k_service = sign(k_region, service)
            k_signing = sign(k_service, 'aws4_request')
            signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
            
            return f'AWS4-HMAC-SHA256 Credential={access_key_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
        
        request_headers = {
            'x-amz-date': now,
            'x-amz-security-token': session_token
        }
        
        authorization = create_signature('GET', apply_url, request_headers, access_key_id, secret_access_key, session_token)
        
        logger.info(f"申请上传权限: {apply_url}")
        
        # 发送申请上传权限请求
        apply_headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'authorization': authorization,
            'origin': 'https://jimeng.jianying.com',
            'referer': 'https://jimeng.jianying.com/ai-tool/image/generate',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'x-amz-date': now,
            'x-amz-security-token': session_token,
        }
        
        import requests
        apply_response = requests.get(apply_url, headers=apply_headers)
        
        if not apply_response.ok:
            raise Exception(f"申请上传权限失败: {apply_response.status_code} - {apply_response.text}")
        
        apply_result = apply_response.json()
        
        if apply_result.get('ResponseMetadata', {}).get('Error'):
            raise Exception(f"申请上传权限失败: {apply_result['ResponseMetadata']['Error']}")
        
        logger.info("申请上传权限成功")
        
        # 解析上传信息
        upload_address = apply_result.get('Result', {}).get('UploadAddress')
        if not upload_address or not upload_address.get('StoreInfos') or not upload_address.get('UploadHosts'):
            raise Exception(f"获取上传地址失败: {apply_result}")
        
        store_info = upload_address['StoreInfos'][0]
        upload_host = upload_address['UploadHosts'][0]
        auth = store_info['Auth']
        
        upload_url = f"https://{upload_host}/upload/v1/{store_info['StoreUri']}"
        image_id = store_info['StoreUri'].split('/')[-1]
        
        logger.info(f"准备上传图片: image_id={image_id}, upload_url={upload_url}")
        
        # 上传图片文件
        upload_headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Authorization': auth,
            'Connection': 'keep-alive',
            'Content-CRC32': crc32,
            'Content-Disposition': 'attachment; filename="undefined"',
            'Content-Type': 'application/octet-stream',
            'Origin': 'https://jimeng.jianying.com',
            'Referer': 'https://jimeng.jianying.com/ai-tool/image/generate',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'X-Storage-U': '704135154117550',
        }
        
        upload_response = requests.post(upload_url, headers=upload_headers, data=image_data)
        
        if not upload_response.ok:
            raise Exception(f"图片上传失败: {upload_response.status_code} - {upload_response.text}")
        
        logger.info("图片文件上传成功")
        
        # 提交上传
        commit_url = f"{apply_url_host}/?Action=CommitImageUpload&Version=2018-08-01&ServiceId={service_id}"
        
        commit_timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        commit_payload = json.dumps({
            "SessionKey": upload_address['SessionKey'],
            "SuccessActionStatus": "200"
        })
        
        payload_hash = hashlib.sha256(commit_payload.encode('utf-8')).hexdigest()
        
        commit_request_headers = {
            'x-amz-date': commit_timestamp,
            'x-amz-security-token': session_token,
            'x-amz-content-sha256': payload_hash
        }
        
        commit_authorization = create_signature('POST', commit_url, commit_request_headers, access_key_id, secret_access_key, session_token, commit_payload)
        
        commit_headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'authorization': commit_authorization,
            'content-type': 'application/json',
            'origin': 'https://jimeng.jianying.com',
            'referer': 'https://jimeng.jianying.com/ai-tool/image/generate',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'x-amz-date': commit_timestamp,
            'x-amz-security-token': session_token,
            'x-amz-content-sha256': payload_hash,
        }
        
        commit_response = requests.post(commit_url, headers=commit_headers, data=commit_payload.encode('utf-8'))
        
        if not commit_response.ok:
            raise Exception(f"提交上传失败: {commit_response.status_code} - {commit_response.text}")
        
        commit_result = commit_response.json()
        
        if commit_result.get('ResponseMetadata', {}).get('Error'):
            raise Exception(f"提交上传失败: {commit_result['ResponseMetadata']['Error']}")
        
        if not commit_result.get('Result', {}).get('Results') or len(commit_result['Result']['Results']) == 0:
            raise Exception(f"提交上传响应缺少结果: {commit_result}")
        
        upload_result = commit_result['Result']['Results'][0]
        if upload_result.get('UriStatus') != 2000:
            raise Exception(f"图片上传状态异常: UriStatus={upload_result.get('UriStatus')}")
        
        full_image_uri = upload_result['Uri']
        
        # 验证图片信息
        plugin_result = commit_result.get('Result', {}).get('PluginResult', [{}])[0]
        if plugin_result and plugin_result.get('ImageUri'):
            logger.info(f"图片上传完成: {plugin_result['ImageUri']}")
            return plugin_result['ImageUri']
        
        logger.info(f"图片上传完成: {full_image_uri}")
        return full_image_uri
    except Exception as e:
        logger.error(f"图片Buffer上传失败: {str(e)}")
        raise e


def generate_images(
    _model: str,
    prompt: str,
    options: Dict[str, Any],
    refresh_token: str
) -> List[str]:
    """生成图像"""
    # 判断是否为US地区
    is_us = refresh_token.lower().startswith('us-')
    model = get_model(_model, is_us)  # 与TS保持一致
    
    # 处理不同的参数格式
    if "width" in options and "height" in options:
        # 从width和height计算ratio和resolution
        width = options["width"]
        height = options["height"]
        # 计算最大公约数以简化比例
        def gcd(a, b):
            return a if b == 0 else gcd(b, a % b)
        divisor = gcd(width, height)
        simplified_width = width // divisor
        simplified_height = height // divisor
        ratio = f"{simplified_width}:{simplified_height}"
        # 简化处理，固定使用2k分辨率
        resolution = "2k"
        sample_strength = options.get("sampleStrength", 0.5)
        negative_prompt = options.get("negativePrompt", "")
    else:
        # 使用标准参数
        ratio = options.get("ratio", "1:1")
        resolution = options.get("resolution", "2k")
        sample_strength = options.get("sampleStrength", 0.5)
        negative_prompt = options.get("negativePrompt", "")
    
    logger.info(f"使用模型: {_model} 映射模型: {model} 分辨率: {resolution} 比例: {ratio} 精细度: {sample_strength}")
    
    # 获取积分信息
    try:
        credit_info = get_credit(refresh_token)
        if credit_info["totalCredit"] <= 0:
            receive_credit(refresh_token)
    except Exception as e:
        logger.warn(f"获取积分失败，可能是不支持的区域或token已失效: {str(e)}")
    
    # 获取分辨率参数
    params = get_resolution_params(resolution, ratio)
    width = params["width"]
    height = params["height"]
    image_ratio = params["image_ratio"]
    resolution_type = params["resolution_type"]
    
    component_id = uuid_generator()
    
    # 生成随机种子，与TS保持一致
    import random
    seed = random.randint(0, 99999999) + 2500000000
    
    core_param = {
        "type": "",
        "id": uuid_generator(),
        "model": model,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,  # 与TS保持一致
        "sample_strength": sample_strength,
        "image_ratio": image_ratio,
        "large_image_info": {
            "type": "",
            "id": uuid_generator(),
            "height": height,
            "width": width,
            "resolution_type": resolution_type
        },
        "intelligent_ratio": False
    }
    
    # 构建draft_content
    draft_content = {
        "type": "draft",
        "id": uuid_generator(),
        "min_version": DRAFT_MIN_VERSION,
        "min_features": [],
        "is_from_tsn": True,
        "version": DRAFT_VERSION,
        "main_component_id": component_id,
        "component_list": [
            {
                "type": "image_base_component",
                "id": component_id,
                "min_version": DRAFT_MIN_VERSION,
                "aigc_mode": "workbench",
                "metadata": {
                    "type": "",
                    "id": uuid_generator(),
                    "created_platform": 3,
                    "created_platform_version": "",
                    "created_time_in_ms": str(int(time.time() * 1000)),  # 与TS保持一致
                    "created_did": ""
                },
                "generate_type": "generate",
                "abilities": {
                    "type": "",
                    "id": uuid_generator(),
                    "generate": {
                        "type": "",
                        "id": uuid_generator(),
                        "core_param": core_param,
                    },
                },
            },
        ],
    }
    
    # 构建metrics_extra
    metrics_extra = {
        "promptSource": "custom",
        "generateCount": 1,
        "enterFrom": "click",
        "generateId": uuid_generator(),
        "isRegenerate": False
    }
    
    # 判断是否为US地区
    is_us = refresh_token.lower().startswith('us-')
    aid = DEFAULT_ASSISTANT_ID_US if is_us else DEFAULT_ASSISTANT_ID_CN
    
    # 发送生成请求，使用与TS项目相同的参数结构
    result = request_api(
        "post",
        "/mweb/v1/aigc_draft/generate",
        refresh_token,
        {
            "params": {},  # 与TS项目保持一致，params为空对象
            "data": {
                "extend": {
                    "root_model": model,
                },
                "submit_id": uuid_generator(),
                "metrics_extra": json.dumps(metrics_extra, separators=(',', ':')),  # 确保是字符串
                "draft_content": json.dumps(draft_content, separators=(',', ':')),  # 确保是字符串
                "http_common_info": {
                    "aid": aid  # 根据地区动态设置aid
                }
            },
        }
    )
    
    # 检查响应格式并提取图片URL
    image_urls = []
    if isinstance(result, dict):
        # 尝试从不同可能的字段中提取图片URL
        aigc_data = result.get("data", {}).get("aigc_data", {}) if "data" in result else result.get("aigc_data", {})
        history_id = aigc_data.get("history_record_id")
        
        if history_id:
            # 实现轮询逻辑
            max_attempts = 900  # 最多轮询900次，与TS保持一致
            
            # 使用与generateImages函数中相同的轮询逻辑
            last_item_count = 0
            stable_rounds = 0
            expected_item_count = 4  # 期望的图片数量
            
            for attempt in range(max_attempts):
                try:
                    time.sleep(2)  # 等待2秒再查询
                    poll_result = request_api(
                        "post",
                        "/mweb/v1/get_history_by_ids",
                        refresh_token,
                        {
                            "data": {
                                "history_ids": [history_id],
                                "image_info": {
                                    "width": 2048,
                                    "height": 2048,
                                    "format": "webp",
                                    "image_scene_list": [
                                        {"scene": "smart_crop", "width": 360, "height": 360, "uniq_key": "smart_crop-w:360-h:360", "format": "webp"},
                                        {"scene": "smart_crop", "width": 480, "height": 480, "uniq_key": "smart_crop-w:480-h:480", "format": "webp"},
                                        {"scene": "smart_crop", "width": 720, "height": 720, "uniq_key": "smart_crop-w:720-h:720", "format": "webp"},
                                        {"scene": "smart_crop", "width": 720, "height": 480, "uniq_key": "smart_crop-w:720-h:480", "format": "webp"},
                                        {"scene": "smart_crop", "width": 360, "height": 240, "uniq_key": "smart_crop-w:360-h:240", "format": "webp"},
                                        {"scene": "smart_crop", "width": 240, "height": 320, "uniq_key": "smart_crop-w:240-h:320", "format": "webp"},
                                        {"scene": "smart_crop", "width": 480, "height": 640, "uniq_key": "smart_crop-w:480-h:640", "format": "webp"},
                                        {"scene": "normal", "width": 2400, "height": 2400, "uniq_key": "2400", "format": "webp"},
                                        {"scene": "normal", "width": 1080, "height": 1080, "uniq_key": "1080", "format": "webp"},
                                        {"scene": "normal", "width": 720, "height": 720, "uniq_key": "720", "format": "webp"},
                                        {"scene": "normal", "width": 480, "height": 480, "uniq_key": "480", "format": "webp"},
                                        {"scene": "normal", "width": 360, "height": 360, "uniq_key": "360", "format": "webp"},
                                    ],
                                }
                            },
                        }
                    )
                    
                    if isinstance(poll_result, dict):
                        # 从响应中提取历史记录数据
                        logger.info(f"完整响应数据类型: {type(poll_result)}")
                        logger.info(f"poll_result键名: {list(poll_result.keys()) if isinstance(poll_result, dict) else 'Not a dict'}")
                        
                        # 检查data字段
                        data_field = poll_result.get("data", {})
                        logger.info(f"data字段类型: {type(data_field)}")
                        logger.info(f"data字段键名: {list(data_field.keys()) if isinstance(data_field, dict) else 'Not a dict'}")
                        
                        # 获取history_data
                        history_data = data_field.get(history_id, {}) if isinstance(data_field, dict) else {}
                        logger.info(f"history_data类型: {type(history_data)}")
                        
                        item_list = history_data.get("item_list", [])
                        status = history_data.get("status", 20)  # 默认为处理中
                        item_count = len(item_list)
                        
                        # 日志输出轮询状态和部分响应数据，用于调试
                        logger.info(f"轮询 {attempt+1}/{max_attempts}: status={status}, items={item_count}")
                        # 输出部分响应数据用于调试（不仅限于前几次轮询）
                        # 更详细地输出响应数据结构
                        history_keys = list(history_data.keys()) if isinstance(history_data, dict) else []
                        logger.info(f"响应数据键名: {history_keys}")
                        # 输出部分history_data内容用于调试
                        if isinstance(history_data, dict):
                            logger.info(f"history_data部分内容: {str(history_data)[:500]}...")
                        
                        # 提取当前轮询中的图片URL
                        current_urls = []
                        
                        # 首先尝试从item_list中提取图片URL
                        for item in item_list:
                            # 尝试从不同路径提取图片URL
                            image_url = None
                            if item.get("image", {}).get("large_images", []):
                                image_url = item["image"]["large_images"][0].get("image_url")
                            elif item.get("common_attr", {}).get("cover_url"):
                                image_url = item["common_attr"]["cover_url"]
                            elif item.get("image_url"):
                                image_url = item["image_url"]
                            elif item.get("url"):
                                image_url = item["url"]
                            
                            if image_url:
                                current_urls.append(image_url)
                        
                        # 如果item_list中没有找到图片URL，尝试直接从history_data中查找
                        if not current_urls:
                            # 检查history_data中是否有直接的图片URL字段
                            if history_data.get("common_attr", {}).get("cover_url"):
                                current_urls.append(history_data["common_attr"]["cover_url"])
                            # 检查是否有其他可能包含图片URL的字段
                            cover_url = history_data.get("cover_url")
                            if cover_url:
                                current_urls.append(cover_url)
                            # 检查是否有result字段包含图片URL
                            result_data = history_data.get("result", {})
                            if isinstance(result_data, dict) and result_data.get("cover_url"):
                                current_urls.append(result_data["cover_url"])
                            # 检查data字段
                            data_field_hd = history_data.get("data", {})
                            if isinstance(data_field_hd, dict) and data_field_hd.get("cover_url"):
                                current_urls.append(data_field_hd["cover_url"])
                            # 检查是否有image字段
                            image_field = history_data.get("image", {})
                            if isinstance(image_field, dict) and image_field.get("cover_url"):
                                current_urls.append(image_field["cover_url"])
                            # 检查是否有asset_option字段
                            asset_option = history_data.get("asset_option", {})
                            if isinstance(asset_option, dict):
                                # 检查asset_option中的cover_url
                                if asset_option.get("cover_url"):
                                    current_urls.append(asset_option["cover_url"])
                                # 检查asset_option中的image_url
                                if asset_option.get("image_url"):
                                    current_urls.append(asset_option["image_url"])
                            # 检查是否有pre_gen_item_ids字段
                            pre_gen_item_ids = history_data.get("pre_gen_item_ids", [])
                            if isinstance(pre_gen_item_ids, list) and len(pre_gen_item_ids) > 0:
                                logger.info(f"发现pre_gen_item_ids: {pre_gen_item_ids}")
                                # 检查每个pre_gen_item_id是否有对应的图片URL
                                for item_id in pre_gen_item_ids:
                                    # 可能需要额外的API调用来获取这些item的详细信息
                                    pass
                        
                        # 更新image_urls集合
                        for url in current_urls:
                            if url not in image_urls:
                                image_urls.append(url)
                                logger.info(f"发现新的图片URL: {url}")
                        
                        # 检查状态码决定是否退出轮询
                        # 状态码说明:
                        # 10: SUCCESS (成功)
                        # 20: PROCESSING (处理中)
                        # 30: FAILED (失败)
                        # 42: POST_PROCESSING (后处理中)
                        # 45: FINALIZING (收尾中)
                        # 50: COMPLETED (已完成)
                        if status == 30:
                            logger.error("任务失败")
                            raise Exception("图像生成失败")
                        elif status == 50:
                            logger.info("任务已完成")
                            break
                        elif status == 10:
                            logger.info("任务成功")
                            # 如果有图片URL则退出
                            if current_urls:
                                break
                        elif status == 45:
                            logger.info("任务收尾中")
                            # 状态45表示收尾阶段，如果有图片URL则退出
                            if current_urls:
                                logger.info("检测到图片URL且状态为收尾阶段，准备退出轮询")
                                break
                            # 即使没有图片URL，状态45也意味着任务接近完成，可以适当减少轮询次数
                            if attempt > 50:  # 超过50次轮询后退出
                                logger.info("状态为收尾阶段且轮询次数过多，退出轮询")
                                break
                        elif status == 42:
                            logger.info("任务后处理中")
                            # 状态42表示后处理阶段，如果有图片URL则可以考虑退出
                            if current_urls and attempt > 5:  # 至少轮询5次后才考虑退出
                                logger.info("检测到图片URL且状态为后处理阶段，准备退出轮询")
                                break
                        
                        # 检查是否已获得期望数量的结果
                        if item_count >= expected_item_count:
                            logger.info(f"已获得完整结果集({item_count}/{expected_item_count})")
                            break
                            
                        # 检查图片数量是否稳定
                        if item_count == last_item_count:
                            stable_rounds += 1
                            if stable_rounds >= 3 and item_count > 0:  # 3轮稳定且有结果
                                logger.info(f"结果数量稳定({stable_rounds}轮)")
                                break
                        else:
                            stable_rounds = 0
                            last_item_count = item_count
                            
                        # 如果已经有图片URL且轮询次数较多，可以提前退出
                        if len(image_urls) > 0 and attempt > 10:
                            logger.info("已有图片结果且轮询次数足够，提前退出")
                            break
                            
                except Exception as e:
                    logger.warn(f"轮询第{attempt+1}次失败: {str(e)}")
                    continue
    
    logger.info(f"图像生成完成: 成功生成 {len(image_urls)} 张图片")
    if image_urls:
        logger.info(f"图片URL列表: {image_urls}")
    return image_urls


def generate_image_composition(
    _model: str,
    prompt: str,
    images: List[Union[str, bytes]],
    options: Dict[str, Any],
    refresh_token: str
) -> List[str]:
    """生成图像合成"""
    model = get_model(_model)
    ratio = options.get("ratio", "1:1")
    resolution = options.get("resolution", "2k")
    sample_strength = options.get("sampleStrength", 0.5)
    negative_prompt = options.get("negativePrompt", "")
    
    # 获取分辨率参数
    params = get_resolution_params(resolution, ratio)
    width = params["width"]
    height = params["height"]
    image_ratio = params["image_ratio"]
    resolution_type = params["resolution_type"]
    
    image_count = len(images)
    logger.info(f"使用模型: {_model} 映射模型: {model} 图生图功能 {image_count}张图片 {width}x{height} 精细度: {sample_strength}")
    
    # 获取积分信息
    try:
        credit_info = get_credit(refresh_token)
        if credit_info["totalCredit"] <= 0:
            receive_credit(refresh_token)
    except Exception as e:
        logger.warn(f"获取积分失败，可能是不支持的区域或token已失效: {str(e)}")
    
    # 上传图片
    uploaded_image_ids = []
    for i, image in enumerate(images):
        try:
            logger.info(f"正在处理第 {i + 1}/{image_count} 张图片...")
            if isinstance(image, str):
                image_id = upload_image_from_url(image, refresh_token)
            else:
                image_id = upload_image_from_buffer(image, refresh_token)
            uploaded_image_ids.append(image_id)
            logger.info(f"图片 {i + 1}/{image_count} 上传成功: {image_id}")
        except Exception as e:
            logger.error(f"图片 {i + 1}/{image_count} 上传失败: {str(e)}")
            raise APIException(EX.API_IMAGE_GENERATION_FAILED, f"图片上传失败: {str(e)}")
    
    logger.info(f"所有图片上传完成，开始图生图: {', '.join(uploaded_image_ids)}")
    
    component_id = uuid_generator()
    submit_id = uuid_generator()
    
    core_param = {
        "type": "",
        "id": uuid_generator(),
        "model": model,
        "prompt": f"##{prompt}",
        "sample_strength": sample_strength,
        "image_ratio": image_ratio,
        "large_image_info": {
            "type": "",
            "id": uuid_generator(),
            "height": height,
            "width": width,
            "resolution_type": resolution_type
        },
        "intelligent_ratio": False,
    }
    
    # 构建draft_content
    draft_content = {
        "type": "draft",
        "id": uuid_generator(),
        "min_version": DRAFT_MIN_VERSION,
        "min_features": [],
        "is_from_tsn": True,
        "version": DRAFT_VERSION,
        "main_component_id": component_id,
        "component_list": [
            {
                "type": "image_base_component",
                "id": component_id,
                "min_version": DRAFT_MIN_VERSION,
                "aigc_mode": "workbench",
                "metadata": {
                    "type": "",
                    "id": uuid_generator(),
                    "created_platform": 3,
                    "created_platform_version": "",
                    "created_time_in_ms": str(int(time.time() * 1000)),
                    "created_did": "",
                },
                "generate_type": "blend",
                "abilities": {
                    "type": "",
                    "id": uuid_generator(),
                    "blend": {
                        "type": "",
                        "id": uuid_generator(),
                        "min_features": [],
                        "core_param": core_param,
                        "ability_list": [
                            {
                                "type": "",
                                "id": uuid_generator(),
                                "name": "byte_edit",
                                "image_uri_list": [image_id],
                                "image_list": [{
                                    "type": "image",
                                    "id": uuid_generator(),
                                    "source_from": "upload",
                                    "platform_type": 1,
                                    "name": "",
                                    "image_uri": image_id,
                                    "width": 0,
                                    "height": 0,
                                    "format": "",
                                    "uri": image_id
                                }],
                                "strength": 0.5
                            } for image_id in uploaded_image_ids
                        ],
                        "prompt_placeholder_info_list": [
                            {
                                "type": "",
                                "id": uuid_generator(),
                                "ability_index": index
                            } for index in range(len(uploaded_image_ids))
                        ],
                        "postedit_param": {
                            "type": "",
                            "id": uuid_generator(),
                            "generate_type": 0
                        }
                    },
                },
            },
        ],
    }
    
    # 构建metrics_extra
    metrics_extra = {
        "promptSource": "custom",
        "generateCount": 1,
        "enterFrom": "click",
        "generateId": submit_id,
        "isRegenerate": False
    }
    
    # 发送生成请求，使用与TS项目相同的参数结构
    result = request_api(
        "post",
        "/mweb/v1/aigc_draft/generate",
        refresh_token,
        {
            "data": {
                "extend": {
                    "root_model": model,
                },
                "submit_id": submit_id,
                "metrics_extra": json.dumps(metrics_extra, separators=(',', ':')),  # 确保是字符串
                "draft_content": json.dumps(draft_content, separators=(',', ':')),  # 确保是字符串
                "http_common_info": {
                    "aid": DEFAULT_ASSISTANT_ID_CN  # 数字类型
                }
            },
        }
    )
    
    # 检查响应格式并提取图片URL
    image_urls = []
    if isinstance(result, dict):
        # 尝试从不同可能的字段中提取图片URL
        aigc_data = result.get("aigc_data", {})
        history_id = aigc_data.get("history_record_id")
        
        if history_id:
            # 实现轮询逻辑
            max_attempts = 30  # 最多轮询30次
            for attempt in range(max_attempts):
                try:
                    time.sleep(2)  # 等待2秒再查询
                    poll_result = request_api(
                        "post",
                        "/mweb/v1/get_history_by_ids",
                        refresh_token,
                        {
                            "data": {
                                "history_ids": [history_id],
                                "image_info": {
                                    "width": 2048,
                                    "height": 2048,
                                    "format": "webp",
                                    "image_scene_list": [
                                        {"scene": "smart_crop", "width": 360, "height": 360, "uniq_key": "smart_crop-w:360-h:360", "format": "webp"},
                                        {"scene": "smart_crop", "width": 480, "height": 480, "uniq_key": "smart_crop-w:480-h:480", "format": "webp"},
                                        {"scene": "smart_crop", "width": 720, "height": 720, "uniq_key": "smart_crop-w:720-h:720", "format": "webp"},
                                        {"scene": "smart_crop", "width": 720, "height": 480, "uniq_key": "smart_crop-w:720-h:480", "format": "webp"},
                                        {"scene": "smart_crop", "width": 360, "height": 240, "uniq_key": "smart_crop-w:360-h:240", "format": "webp"},
                                        {"scene": "smart_crop", "width": 240, "height": 320, "uniq_key": "smart_crop-w:240-h:320", "format": "webp"},
                                        {"scene": "smart_crop", "width": 480, "height": 640, "uniq_key": "smart_crop-w:480-h:640", "format": "webp"},
                                        {"scene": "normal", "width": 2400, "height": 2400, "uniq_key": "2400", "format": "webp"},
                                        {"scene": "normal", "width": 1080, "height": 1080, "uniq_key": "1080", "format": "webp"},
                                        {"scene": "normal", "width": 720, "height": 720, "uniq_key": "720", "format": "webp"},
                                        {"scene": "normal", "width": 480, "height": 480, "uniq_key": "480", "format": "webp"},
                                        {"scene": "normal", "width": 360, "height": 360, "uniq_key": "360", "format": "webp"},
                                    ],
                                }
                            },
                        }
                    )
                    
                    if isinstance(poll_result, dict):
                        # 从响应中提取图片URL
                        history_data = poll_result.get(history_id, {})
                        item_list = history_data.get("item_list", [])
                        
                        for item in item_list:
                            # 尝试从不同路径提取图片URL
                            image_url = None
                            if item.get("image", {}).get("large_images", []):
                                image_url = item["image"]["large_images"][0].get("image_url")
                            elif item.get("common_attr", {}).get("cover_url"):
                                image_url = item["common_attr"]["cover_url"]
                            elif item.get("image_url"):
                                image_url = item["image_url"]
                            elif item.get("url"):
                                image_url = item["url"]
                            
                            if image_url:
                                image_urls.append(image_url)
                        
                        # 如果提取到图片URL，跳出轮询
                        if image_urls:
                            break
                except Exception as e:
                    logger.warn(f"轮询第{attempt+1}次失败: {str(e)}")
                    continue
    
    logger.info(f"图生图结果: 成功生成 {len(image_urls)} 张图片")
    return image_urls
