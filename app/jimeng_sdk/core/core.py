import os
import sys
import time
import hashlib
import uuid
import requests
import json
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..lib.logger import logger
from ..lib.exceptions.api_exception import APIException
from ..lib.consts.exceptions import EX

# 模型名称
MODEL_NAME = "jimeng"
# 设备ID
DEVICE_ID = str(int(time.time() * 1000000) % 1000000000000000000 + 7000000000000000000)
# WebID
WEB_ID = str(int(time.time() * 1000000) % 1000000000000000000 + 7000000000000000000)
# 用户ID
USER_ID = str(uuid.uuid4())
# 伪装headers
FAKE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-language": "zh-CN,zh;q=0.9",
    "Cache-control": "no-cache",
    "Last-event-id": "undefined",
    "Appvr": "7.5.0",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Pf": "11",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
# 文件最大大小
FILE_MAX_SIZE = 100 * 1024 * 1024

# 基础URL
BASE_URL_CN = "https://jimeng.jianying.com"
BASE_URL_US_COMMERCE = "https://jimeng.jianying.com"
BASE_URL_DREAMINA_US = "https://jimeng.jianying.com"
# 默认助手ID
DEFAULT_ASSISTANT_ID_CN = 513695  # 数字类型
DEFAULT_ASSISTANT_ID_US = 513641  # 数字类型
# 区域
REGION_CN = "cn-gd"
REGION_US = "us"
# 版本代码
VERSION_CODE = "7.5.0"
# 平台代码
PLATFORM_CODE = "11"

def acquire_token(refresh_token: str) -> str:
    """获取缓存中的access_token"""
    return refresh_token

def generate_cookie(refresh_token: str) -> str:
    """生成cookie"""
    is_us = refresh_token.lower().startswith('us-')
    token = refresh_token[3:] if is_us else refresh_token
    cookie_parts = [
        f"_tea_web_id={WEB_ID}",
        "is_staff_user=false",
        f"store-region={ 'us' if is_us else 'cn-gd' }",
        "store-region-src=uid",
        f"sid_guard={token}%7C{int(time.time())}%7C5184000%7CMon%2C+03-Feb-2025+08%3A17%3A09+GMT",
        f"uid_tt={USER_ID}",
        f"uid_tt_ss={USER_ID}",
        f"sid_tt={token}",
        f"sessionid={token}",
        f"sessionid_ss={token}",
        f"sid_tt={token}"
    ]
    return "; ".join(cookie_parts)

def token_split(authorization: str) -> List[str]:
    """Token切分"""
    return authorization.replace("Bearer ", "").split(",")

def get_credit(refresh_token: str) -> Dict[str, Any]:
    """获取积分信息"""
    try:
        result = request_api("POST", "/commerce/v1/benefits/user_credit", refresh_token, {
            "data": {},
            "headers": {
                "Referer": "https://jimeng.jianying.com/ai-tool/image/generate",
            },
            "noDefaultParams": True
        })
        
        # 检查返回的数据结构
        if isinstance(result, dict):
            # 首先检查是否有data字段
            if "data" in result and isinstance(result["data"], dict) and "credit" in result["data"]:
                credit_info = result["data"]["credit"]
                gift_credit = credit_info.get("gift_credit", 0)
                purchase_credit = credit_info.get("purchase_credit", 0)
                vip_credit = credit_info.get("vip_credit", 0)
            # 然后检查是否有credit字段（直接在顶层）
            elif "credit" in result:
                credit_info = result["credit"]
                gift_credit = credit_info.get("gift_credit", 0)
                purchase_credit = credit_info.get("purchase_credit", 0)
                vip_credit = credit_info.get("vip_credit", 0)
            else:
                # 如果返回的不是预期的结构，使用默认值
                gift_credit = 0
                purchase_credit = 0
                vip_credit = 0
        else:
            # 如果返回的不是预期的结构，使用默认值
            gift_credit = 0
            purchase_credit = 0
            vip_credit = 0
        
        return {
            "giftCredit": gift_credit,
            "purchaseCredit": purchase_credit,
            "vipCredit": vip_credit,
            "totalCredit": gift_credit + purchase_credit + vip_credit
        }
    except Exception as e:
        logger.warn(f"获取积分失败: {str(e)}")
        return {
            "giftCredit": 0,
            "purchaseCredit": 0,
            "vipCredit": 0,
            "totalCredit": 0
        }

def receive_credit(refresh_token: str) -> int:
    """接收今日积分"""
    try:
        logger.info("正在收取今日积分...")
        result = request_api("POST", "/commerce/v1/benefits/credit_receive", refresh_token, {
            "data": {
                "time_zone": "Asia/Shanghai"
            },
            "headers": {
                "Referer": "https://jimeng.jianying.com/ai-tool/image/generate"
            }
        })
        
        cur_total_credits = result.get("cur_total_credits", 0)
        receive_quota = result.get("receive_quota", 0)
        
        logger.info(f"\n今日{receive_quota}积分收取成功\n剩余积分: {cur_total_credits}")
        return cur_total_credits
    except Exception as e:
        logger.error(f"收取积分失败: {str(e)}")
        return 0

def request_api(
    method: str,
    uri: str,
    refresh_token: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """请求jimeng API"""
    if options is None:
        options = {}
        
    is_us = refresh_token.lower().startswith('us-')
    token = acquire_token(refresh_token[3:] if is_us else refresh_token)
    device_time = int(time.time())
    sign = hashlib.md5(
        f"9e2c|{uri[-7:]}|{PLATFORM_CODE}|{VERSION_CODE}|{device_time}||11ac".encode('utf-8')
    ).hexdigest()

    base_url = BASE_URL_DREAMINA_US if is_us else BASE_URL_CN
    aid = DEFAULT_ASSISTANT_ID_US if is_us else DEFAULT_ASSISTANT_ID_CN
    region = REGION_US if is_us else REGION_CN

    origin = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
    full_url = base_url + uri

    # 处理请求参数
    headers = FAKE_HEADERS.copy()
    headers.update({
        "Origin": origin,
        "Referer": origin,
        "Appid": str(aid),  # 转换为字符串
        "Cookie": generate_cookie(refresh_token),
        "Device-Time": str(device_time),
        "Sign": sign,
        "Sign-Ver": "1",
        # 禁用压缩以避免乱码问题
        "Accept-Encoding": "identity",
    })
    
    # 合并额外头部
    if "headers" in options:
        headers.update(options["headers"])

    # 构建请求参数和数据
    request_params = {}
    request_data = {}
    
    # 处理params字段
    if "params" in options:
        request_params.update(options["params"])
    
    # 处理data字段
    if "data" in options:
        request_data.update(options["data"])
    
    # 只有在noDefaultParams为False时才添加默认参数到请求参数中（与TS项目保持一致）
    # 即使params字段存在但为空{}，也要添加默认参数
    if not options.get("noDefaultParams", False):
        # 添加默认参数到请求参数中（与TS项目的实现保持一致）
        if "aid" not in request_params:
            request_params["aid"] = aid
        if "device_platform" not in request_params:
            request_params["device_platform"] = "web"
        if "region" not in request_params:
            request_params["region"] = region
        if "webId" not in request_params and not is_us:
            request_params["webId"] = WEB_ID
        if "da_version" not in request_params:
            request_params["da_version"] = "3.3.2"
        if "web_component_open_flag" not in request_params:
            request_params["web_component_open_flag"] = 1
        if "web_version" not in request_params:
            request_params["web_version"] = "7.5.0"
        if "aigc_features" not in request_params:
            request_params["aigc_features"] = "app_lip_sync"
    
    logger.info(f"发送请求: {method.upper()} {full_url}")
    logger.info(f"请求参数: {json.dumps(request_params, ensure_ascii=False)}")
    logger.info(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}")

    try:
        response = requests.request(
            method,
            full_url,
            params=request_params,
            headers=headers,
            json=request_data,
            timeout=45,
            # 禁用自动解压
            stream=False
        )
        
        logger.info(f"响应状态: {response.status_code} {response.reason}")
        
        # 记录响应数据摘要
        response_data_summary = response.text[:500] + ("..." if len(response.text) > 500 else "")
        logger.info(f"响应数据摘要: {response_data_summary}")
        
        response.raise_for_status()
        
        # 解析响应
        try:
            result = response.json()
            
            # 检查API返回的错误码
            if isinstance(result, dict):
                ret_code = result.get("ret", "0")
                errmsg = result.get("errmsg", "")
                
                # 如果返回错误码且不是成功状态，抛出异常
                if ret_code != "0" and ret_code != 0:
                    raise APIException(EX.API_REQUEST_FAILED, f"API调用失败: [{ret_code}] {errmsg}")
            
            return result
        except json.JSONDecodeError:
            # 如果不是JSON响应，返回文本
            return {"text": response.text}
    except requests.RequestException as e:
        logger.error(f"请求失败: {str(e)}")
        raise APIException(EX.API_REQUEST_FAILED, f"请求失败: {str(e)}")

def check_file_url(file_url: str):
    """预检查文件URL有效性"""
    if is_base64_data(file_url):
        return
        
    try:
        response = requests.head(file_url, timeout=15)
        if response.status_code >= 400:
            raise APIException(
                EX.API_FILE_URL_INVALID,
                f"File {file_url} is not valid: [{response.status_code}] {response.reason}"
            )
        # 检查文件大小
        if "content-length" in response.headers:
            file_size = int(response.headers["content-length"])
            if file_size > FILE_MAX_SIZE:
                raise APIException(
                    EX.API_FILE_EXECEEDS_SIZE,
                    f"File {file_url} is not valid"
                )
    except requests.RequestException as e:
        raise APIException(
            EX.API_FILE_URL_INVALID,
            f"File {file_url} is not valid: {str(e)}"
        )

def is_base64_data(data: str) -> bool:
    """检查是否为BASE64数据"""
    if not isinstance(data, str):
        return False
    return data.startswith("data:")

def extract_base64_data_format(data: str) -> str:
    """提取BASE64数据格式"""
    if not is_base64_data(data):
        return ""
    return data.split(";")[0].split(":")[1]

def remove_base64_data_header(data: str) -> str:
    """移除BASE64数据头部"""
    if not is_base64_data(data):
        return data
    return data.split(",")[1]