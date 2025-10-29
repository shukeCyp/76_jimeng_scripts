import os
import sys
import time
import uuid
import json
import zlib
import hashlib
import requests
from typing import Any, Dict, List

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..lib.logger import logger
from ..lib.util import uuid_generator
from ..lib.exceptions.api_exception import APIException
from ..lib.consts.exceptions import EX
from .core import request_api, get_credit, receive_credit

# 默认模型
DEFAULT_MODEL = "jimeng-video-3.0"
DEFAULT_VIDEO_MODEL = "jimeng-video-3.0"

# 模型映射
VIDEO_MODEL_MAP = {
    "jimeng-video-3.0": "jimeng-video-3.0",
}

# 常量
DRAFT_VERSION = "3.3.2"
DRAFT_VERSION = "3.3.2"
DRAFT_MIN_VERSION = "3.0.5"
DEFAULT_ASSISTANT_ID_CN = "513695"
DEFAULT_ASSISTANT_ID_US = "513641"
MODEL_MAP = {
    'jimeng-video-3.0': 'dreamina_ic_generate_video_model_vgfm_3.0',
    'jimeng-video-3.0-pro': 'dreamina_ic_generate_video_model_vgfm_3.0_pro',
    'jimeng-video-2.0': 'dreamina_ic_generate_video_model_vgfm_lite',
    'jimeng-video-2.0-pro': 'dreamina_ic_generate_video_model_vgfm1.0'
}

def get_model(model: str) -> str:
    """获取模型"""
    return MODEL_MAP.get(model, MODEL_MAP[DEFAULT_MODEL])

def calculate_crc32(data: bytes) -> str:
    """计算CRC32"""
    return format(zlib.crc32(data) & 0xffffffff, '08x')

def upload_image_buffer(image_data: bytes, refresh_token: str) -> str:
    """上传图像缓冲区"""
    try:
        # 获取上传令牌
        token_result = request_api("post", "/mweb/v1/get_upload_token", refresh_token, {
            "data": {
                "scene": 2,  # AIGC 图片上传场景
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
        
        logger.info(f"图片Buffer准备完成: 大小={file_size}字节, CRC32={crc32}")
        
        # 申请上传权限
        now = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        random_str = uuid_generator()[:10]
        apply_url = f"https://imagex.bytedanceapi.com/?Action=ApplyImageUpload&Version=2018-08-01&ServiceId={service_id}&FileSize={file_size}&s={random_str}"
        
        # 实现AWS4-HMAC-SHA256签名算法
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
            def sign(key, msg):
                return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
            
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
            'referer': 'https://jimeng.jianying.com/ai-tool/video/generate',
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
            'Referer': 'https://jimeng.jianying.com/ai-tool/video/generate',
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
        commit_url = f"https://imagex.bytedanceapi.com/?Action=CommitImageUpload&Version=2018-08-01&ServiceId={service_id}"
        
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
            'referer': 'https://jimeng.jianying.com/ai-tool/video/generate',
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
            logger.info(f"视频图片上传完成: {plugin_result['ImageUri']}")
            return plugin_result['ImageUri']
        
        logger.info(f"视频图片上传完成: {full_image_uri}")
        return full_image_uri
    except Exception as e:
        logger.error(f"视频图片上传失败: {str(e)}")
        raise e

def upload_image_from_url(image_url: str, refresh_token: str) -> str:
    """从URL上传图像"""
    try:
        logger.info(f"开始从URL下载并上传视频图片: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content
        return upload_image_buffer(image_data, refresh_token)
    except Exception as e:
        logger.error(f"从URL上传视频图片失败: {str(e)}")
        raise e

def upload_image_from_file(file_path: str, refresh_token: str) -> str:
    """从文件上传图像"""
    try:
        logger.info(f"开始从本地文件上传视频图片: {file_path}")
        with open(file_path, 'rb') as f:
            image_data = f.read()
        return upload_image_buffer(image_data, refresh_token)
    except Exception as e:
        logger.error(f"从本地文件上传视频图片失败: {str(e)}")
        raise e

def generate_video(
    _model: str,
    prompt: str,
    options: Dict[str, Any],
    refresh_token: str
) -> str:
    """生成视频"""
    model = get_model(_model)
    width = options.get("width", 1024)
    height = options.get("height", 1024)
    resolution = options.get("resolution", "720p")
    file_paths = options.get("filePaths", [])
    files = options.get("files", {})
    duration_ms = options.get("duration_ms", 5000)
    
    logger.info(f"使用模型: {_model} 映射模型: {model} {width}x{height} 分辨率: {resolution}")

    # 检查积分
    try:
        credit_info = get_credit(refresh_token)
        if credit_info["totalCredit"] <= 0:
            receive_credit(refresh_token)
    except Exception as e:
        logger.warn(f"获取积分失败，可能是不支持的区域或token已失效: {str(e)}")

    # 处理首帧和尾帧图片
    first_frame_image = None
    end_frame_image = None
    upload_ids = []

    # 优先处理本地上传的文件
    uploaded_files = list(files.values()) if hasattr(files, 'values') else []
    if uploaded_files and len(uploaded_files) > 0:
        logger.info(f"检测到 {len(uploaded_files)} 个本地上传文件，优先处理")
        for i, file in enumerate(uploaded_files):
            if not file:
                continue
            try:
                logger.info(f"开始上传第 {i + 1} 张本地图片")
                # 这里需要根据实际文件对象结构调整
                image_uri = upload_image_from_file(file.get('filepath', ''), refresh_token) if isinstance(file, dict) else upload_image_from_file(str(file), refresh_token)
                if image_uri:
                    upload_ids.append(image_uri)
                    logger.info(f"第 {i + 1} 张本地图片上传成功: {image_uri}")
                else:
                    logger.error(f"第 {i + 1} 张本地图片上传失败: 未获取到 image_uri")
            except Exception as e:
                logger.error(f"第 {i + 1} 张本地图片上传失败: {str(e)}")
                if i == 0:
                    raise APIException(EX.API_REQUEST_FAILED, f"首帧图片上传失败: {str(e)}")
    # 如果没有本地文件，再处理URL
    elif file_paths and len(file_paths) > 0:
        logger.info(f"未检测到本地上传文件，处理 {len(file_paths)} 个图片URL")
        for i, file_path in enumerate(file_paths):
            if not file_path:
                logger.warn(f"第 {i + 1} 个图片URL为空，跳过")
                continue
            try:
                logger.info(f"开始上传第 {i + 1} 个URL图片: {file_path}")
                # 检查是否为本地文件路径
                if os.path.exists(file_path):
                    # 本地文件路径，使用文件上传
                    image_uri = upload_image_from_file(file_path, refresh_token)
                else:
                    # URL路径，使用URL上传
                    image_uri = upload_image_from_url(file_path, refresh_token)
                if image_uri:
                    upload_ids.append(image_uri)
                    logger.info(f"第 {i + 1} 个图片上传成功: {image_uri}")
                else:
                    logger.error(f"第 {i + 1} 个图片上传失败: 未获取到 image_uri")
            except Exception as e:
                logger.error(f"第 {i + 1} 个图片上传失败: {str(e)}")
                if i == 0:
                    raise APIException(EX.API_REQUEST_FAILED, f"首帧图片上传失败: {str(e)}")
    else:
        logger.info("未提供图片文件或URL，将进行纯文本视频生成")

    # 如果有图片上传（无论来源），构建对象
    if len(upload_ids) > 0:
        logger.info(f"图片上传完成，共成功 {len(upload_ids)} 张")
        # 构建首帧图片对象
        if len(upload_ids) > 0 and upload_ids[0]:
            first_frame_image = {
                "format": "",
                "height": height,
                "id": uuid_generator(),
                "image_uri": upload_ids[0],
                "name": "",
                "platform_type": 1,
                "source_from": "upload",
                "type": "image",
                "uri": upload_ids[0],
                "width": width,
            }
            logger.info(f"设置首帧图片: {upload_ids[0]}")
        
        # 构建尾帧图片对象
        if len(upload_ids) > 1 and upload_ids[1]:
            end_frame_image = {
                "format": "",
                "height": height,
                "id": uuid_generator(),
                "image_uri": upload_ids[1],
                "name": "",
                "platform_type": 1,
                "source_from": "upload",
                "type": "image",
                "uri": upload_ids[1],
                "width": width,
            }
            logger.info(f"设置尾帧图片: {upload_ids[1]}")

    component_id = uuid_generator()
    metrics_extra_dict = {
        "enterFrom": "click",
        "isDefaultSeed": 1,
        "promptSource": "custom",
        "isRegenerate": False,
        "originSubmitId": uuid_generator(),
    }
    metrics_extra = json.dumps(metrics_extra_dict, separators=(',', ':'))
    
    # 计算视频宽高比
    def gcd(a, b):
        return a if b == 0 else gcd(b, a % b)
    
    divisor = gcd(width, height)
    aspect_ratio = f"{width // divisor}:{height // divisor}"
    
    # 发送生成请求，使用与TS项目相同的参数结构
    result = request_api(
        "post",
        "/mweb/v1/aigc_draft/generate",
        refresh_token,
        {
            "params": {
                "aigc_features": "app_lip_sync",
                "web_version": "6.6.0",
                "da_version": DRAFT_VERSION,
            },
            "data": {
                "extend": {
                    "root_model": end_frame_image and MODEL_MAP.get('jimeng-video-3.0') or model,
                    "m_video_commerce_info": {
                        "benefit_type": "basic_video_operation_vgfm_v_three",
                        "resource_id": "generate_video",
                        "resource_id_type": "str",
                        "resource_sub_type": "aigc"
                    },
                    "m_video_commerce_info_list": [{
                        "benefit_type": "basic_video_operation_vgfm_v_three",
                        "resource_id": "generate_video",
                        "resource_id_type": "str",
                        "resource_sub_type": "aigc"
                    }]
                },
                "submit_id": uuid_generator(),
                "metrics_extra": metrics_extra,
                "draft_content": json.dumps({
                    "type": "draft",
                    "id": uuid_generator(),
                    "min_version": "3.0.5",
                    "is_from_tsn": True,
                    "version": DRAFT_VERSION,
                    "main_component_id": component_id,
                    "component_list": [{
                        "type": "video_base_component",
                        "id": component_id,
                        "min_version": "1.0.0",
                        "metadata": {
                            "type": "",
                            "id": uuid_generator(),
                            "created_platform": 3,
                            "created_platform_version": "",
                            "created_time_in_ms": int(time.time() * 1000),
                            "created_did": ""
                        },
                        "generate_type": "gen_video",
                        "aigc_mode": "workbench",
                        "abilities": {
                            "type": "",
                            "id": uuid_generator(),
                            "gen_video": {
                                "id": uuid_generator(),
                                "type": "",
                                "text_to_video_params": {
                                    "type": "",
                                    "id": uuid_generator(),
                                    "model_req_key": model,
                                    "priority": 0,
                                    "seed": int(time.time() * 1000) % 100000000 + 2500000000,
                                    "video_aspect_ratio": aspect_ratio,
                                    "video_gen_inputs": [{
                                        "duration_ms": duration_ms,
                                        "first_frame_image": first_frame_image,
                                        "end_frame_image": end_frame_image,
                                        "fps": 24,
                                        "id": uuid_generator(),
                                        "min_version": "3.0.5",
                                        "prompt": prompt,
                                        "resolution": resolution,
                                        "type": "",
                                        "video_mode": 2
                                    }]
                                },
                                "video_task_extra": metrics_extra,
                            }
                        }
                    }],
                }, separators=(',', ':')),
                "http_common_info": {
                    "aid": int(DEFAULT_ASSISTANT_ID_CN),
                },
            },
        }
    )

    # 从响应中提取视频URL
    video_url = ""
    if isinstance(result, dict):
        # 尝试从不同可能的字段中提取视频URL
        aigc_data = result.get("data", {}).get("aigc_data", {}) if "data" in result else result.get("aigc_data", {})
        history_id = aigc_data.get("history_record_id")
        
        if history_id:
            # 实现轮询逻辑
            status = 20
            fail_code = None
            item_list = []
            retry_count = 0
            max_retries = 60  # 增加重试次数，支持约20分钟的总重试时间
            
            # 首次查询前等待更长时间，让服务器有时间处理请求
            time.sleep(5)
            
            logger.info(f"开始轮询视频生成结果，历史ID: {history_id}，最大重试次数: {max_retries}")
            logger.info("即梦官网API地址: https://jimeng.jianying.com/mweb/v1/get_history_by_ids")
            logger.info("视频生成请求已发送，请同时在即梦官网查看: https://jimeng.jianying.com/ai-tool/video/generate")
            
            while status == 20 and retry_count < max_retries:
                try:
                    # 尝试两种不同的API请求方式
                    use_alternative_api = retry_count > 10 and retry_count % 2 == 0  # 在重试10次后，每隔一次尝试备用API
                    
                    if use_alternative_api:
                        # 备用API请求方式
                        logger.info(f"尝试备用API请求方式，历史ID: {history_id}, 重试次数: {retry_count + 1}/{max_retries}")
                        poll_result = request_api(
                            "post",
                            "/mweb/v1/get_history_records",
                            refresh_token,
                            {
                                "params": {
                                    "aid": int(DEFAULT_ASSISTANT_ID_CN),
                                    "device_platform": "web",
                                    "region": "cn-gd",
                                    "webId": "7001761712929926236",
                                    "da_version": DRAFT_VERSION,
                                    "web_component_open_flag": 1,
                                    "web_version": "7.5.0",
                                    "aigc_features": "app_lip_sync"
                                },
                                "data": {
                                    "history_record_ids": [history_id],
                                },
                            }
                        )
                        
                        # 尝试直接从响应中提取视频URL
                        if isinstance(poll_result, dict):
                            response_str = str(poll_result)
                            import re
                            video_url_match = re.search(r'https://v[0-9]+-artist\.vlabvod\.com/[^"\s]+', response_str)
                            if video_url_match and video_url_match.group(0):
                                logger.info(f"从备用API响应中直接提取到视频URL: {video_url_match.group(0)}")
                                # 提前返回找到的URL
                                video_url = video_url_match.group(0)
                                break
                    else:
                        # 标准API请求方式
                        logger.info(f"发送请求获取视频生成结果，历史ID: {history_id}, 重试次数: {retry_count + 1}/{max_retries}")
                        poll_result = request_api(
                            "post",
                            "/mweb/v1/get_history_by_ids",
                            refresh_token,
                            {
                                "params": {
                                    "aid": int(DEFAULT_ASSISTANT_ID_CN),
                                    "device_platform": "web",
                                    "region": "cn-gd",
                                    "webId": "7001761712929926236",
                                    "da_version": DRAFT_VERSION,
                                    "web_component_open_flag": 1,
                                    "web_version": "7.5.0",
                                    "aigc_features": "app_lip_sync"
                                },
                                "data": {
                                    "history_ids": [history_id],
                                },
                            }
                        )
                        
                        # 尝试直接从响应中提取视频URL
                        if isinstance(poll_result, dict):
                            response_str = str(poll_result)
                            import re
                            video_url_match = re.search(r'https://v[0-9]+-artist\.vlabvod\.com/[^"\s]+', response_str)
                            if video_url_match and video_url_match.group(0):
                                logger.info(f"从标准API响应中直接提取到视频URL: {video_url_match.group(0)}")
                                # 提前返回找到的URL
                                video_url = video_url_match.group(0)
                                break
                    
                    # 检查结果是否有效
                    history_data = None
                    
                    if isinstance(poll_result, dict):
                        if use_alternative_api and poll_result.get("history_records") and len(poll_result["history_records"]) > 0:
                            # 处理备用API返回的数据格式
                            history_data = poll_result["history_records"][0]
                            logger.info("从备用API获取到历史记录")
                        elif poll_result.get("history_list") and len(poll_result["history_list"]) > 0:
                            # 处理标准API返回的数据格式
                            history_data = poll_result["history_list"][0]
                            logger.info("从标准API获取到历史记录")
                        elif poll_result.get("data") and isinstance(poll_result["data"], dict) and poll_result["data"].get(history_id):
                            # 处理另一种可能的数据格式
                            history_data = poll_result["data"][history_id]
                            logger.info("从标准API获取到历史记录（data格式）")
                    
                    if not history_data:
                        # 两种API都没有返回有效数据
                        logger.warn(f"历史记录不存在，重试中 ({retry_count + 1}/{max_retries})... 历史ID: {history_id}")
                        logger.info("请同时在即梦官网检查视频是否已生成: https://jimeng.jianying.com/ai-tool/video/generate")
                        
                        retry_count += 1
                        # 增加重试间隔时间，但设置上限为30秒
                        wait_time = min(2000 * (retry_count + 1), 30000)
                        logger.info(f"等待 {wait_time}ms 后进行第 {retry_count + 1} 次重试")
                        time.sleep(wait_time / 1000.0)
                        continue
                    
                    # 记录获取到的结果详情
                    logger.info(f"获取到历史记录结果: {str(history_data)[:200]}...")
                    
                    # 从历史数据中提取状态和结果
                    status = history_data.get("status", 20)  # 默认为处理中
                    fail_code = history_data.get("fail_code")
                    item_list = history_data.get("item_list", [])
                    
                    logger.info(f"视频生成状态: {status}, 失败代码: {fail_code or '无'}, 项目列表长度: {len(item_list)}")
                    
                    # 如果有视频URL，提前记录
                    temp_video_url = None
                    if len(item_list) > 0:
                        item = item_list[0]
                        if item.get("video", {}).get("transcoded_video", {}).get("origin", {}).get("video_url"):
                            temp_video_url = item["video"]["transcoded_video"]["origin"]["video_url"]
                        elif item.get("video", {}).get("play_url"):
                            temp_video_url = item["video"]["play_url"]
                        elif item.get("video", {}).get("download_url"):
                            temp_video_url = item["video"]["download_url"]
                        elif item.get("video", {}).get("url"):
                            temp_video_url = item["video"]["url"]
                    
                    if temp_video_url:
                        logger.info(f"检测到视频URL: {temp_video_url}")
                    
                    if status == 30:
                        if fail_code == 2038:
                            logger.error("视频生成失败，内容被过滤")
                            raise APIException(EX.API_CONTENT_FILTERED, "内容被过滤")
                        else:
                            logger.error(f"视频生成失败，错误码: {fail_code}")
                            raise APIException(EX.API_IMAGE_GENERATION_FAILED, f"生成失败，错误码: {fail_code}")
                    
                    # 如果状态仍在处理中，等待后继续
                    if status == 20:
                        wait_time = 2000 * (min(retry_count + 1, 5))  # 随着重试次数增加等待时间，但最多10秒
                        logger.info(f"视频生成中，状态码: {status}，等待 {wait_time}ms 后继续查询")
                        time.sleep(wait_time / 1000.0)
                        
                    retry_count += 1
                    
                except Exception as e:
                    logger.error(f"轮询视频生成结果出错: {str(e)}")
                    retry_count += 1
                    time.sleep(2000 * (retry_count + 1) / 1000.0)
            
            # 如果达到最大重试次数仍未成功
            if retry_count >= max_retries and status == 20:
                logger.error(f"视频生成超时，已尝试 {retry_count} 次")
                raise APIException(EX.API_IMAGE_GENERATION_FAILED, "获取视频生成结果超时，请稍后在即梦官网查看您的视频")
            
            # 提取视频URL
            if len(item_list) > 0:
                item = item_list[0]
                if item.get("video", {}).get("transcoded_video", {}).get("origin", {}).get("video_url"):
                    video_url = item["video"]["transcoded_video"]["origin"]["video_url"]
                elif item.get("video", {}).get("play_url"):
                    video_url = item["video"]["play_url"]
                    logger.info(f"从play_url获取到视频URL: {video_url}")
                elif item.get("video", {}).get("download_url"):
                    video_url = item["video"]["download_url"]
                    logger.info(f"从download_url获取到视频URL: {video_url}")
                elif item.get("video", {}).get("url"):
                    video_url = item["video"]["url"]
                    logger.info(f"从url获取到视频URL: {video_url}")
            
            if not video_url:
                logger.error(f"未能获取视频URL，item_list: {item_list}")
                raise APIException(EX.API_IMAGE_GENERATION_FAILED, "未能获取视频URL，请稍后在即梦官网查看")
    
    if not video_url:
        raise APIException(EX.API_IMAGE_GENERATION_FAILED, "视频生成失败，未获取到视频URL")

    logger.info(f"视频生成成功，URL: {video_url}")
    return video_url