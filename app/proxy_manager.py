"""
Proxy Manager

提供从 Clash Verge (Clash 外部控制端) 获取所有节点信息的函数。

默认连接到本机 `http://127.0.0.1:9097`，并使用密码 `abc123456`。
确保 Clash 或 Clash Verge 的配置中已启用：
  external-controller: 127.0.0.1:9097
  secret: abc123456
"""

from typing import Any, Dict, Optional
import json
import urllib.request
import urllib.error
import re


def get_all_clash_verge_nodes(
    host: str = "127.0.0.1",
    port: int = 9097,
    secret: str = "abc123456",
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """
    获取 Clash Verge 的所有节点信息。

    返回结构包含：
      - proxies: 来自 `/proxies` 的字典（名称 -> 详细信息）
      - providers: 来自 `/providers/proxies` 的字典（若支持）
      - nodes: 过滤后的叶子节点列表（剔除 Selector/URLTest/Direct 等组或特殊项）
      - raw: `/proxies` 的原始响应（便于调试）

    参数：
      host: 外部控制端主机，默认 `127.0.0.1`
      port: 外部控制端端口，默认 `9097`
      secret: 访问密钥，默认 `abc123456`
      timeout: 请求超时时间（秒）
    """

    base = f"http://{host}:{port}"
    headers = {
        "Authorization": f"Bearer {secret}",
        "Accept": "application/json",
    }

    def _get(path: str) -> Optional[Dict[str, Any]]:
        req = urllib.request.Request(base + path, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                return json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError:
            # 404 或其他 HTTP 错误时返回 None（例如部分实现不支持 providers）
            return None
        except Exception:
            # 连接失败、解析失败等情况
            return None

    proxies_json = _get("/proxies")
    providers_json = _get("/providers/proxies")

    proxies_dict: Dict[str, Any] = {}
    if isinstance(proxies_json, dict):
        proxies_dict = proxies_json.get("proxies", proxies_json) or {}

    result: Dict[str, Any] = {
        "proxies": proxies_dict,
        "raw": proxies_json or {},
        "providers": {},
    }

    if isinstance(providers_json, dict):
        # Clash Meta 通常返回 { "providers": { ... } }
        result["providers"] = providers_json.get("providers", providers_json) or {}

    # 过滤出叶子节点（排除组、测试、直连/拒绝等）
    exclude_types = {"Selector", "URLTest", "Fallback", "LoadBalance", "Relay", "Direct", "Reject"}
    nodes = []
    for name, info in proxies_dict.items():
        if not isinstance(info, dict):
            continue
        type_ = info.get("type")
        if isinstance(type_, str) and type_ not in exclude_types:
            node: Dict[str, Any] = {"name": name, "type": type_}
            # 拓展若存在的字段
            for k in ("udp", "alive", "history", "delay"):
                if k in info:
                    node[k] = info[k]
            nodes.append(node)

    result["nodes"] = nodes
    return result


def get_current_connected_node(
    host: str = "127.0.0.1",
    port: int = 9097,
    secret: str = "abc123456",
    timeout: float = 5.0,
):
    """
    获取当前所选/连接的节点信息（基于 /proxies 的组选择）。

    优先从下列组中读取当前选择：
      - GLOBAL
      - Proxy / PROXY
      - 其他常见的选择组（例如“🔰 节点选择”、“♻ 自动选择”等）

    返回结构：
      - ok: 是否成功获取到当前节点
      - group: 使用的组名称
      - now: 当前节点名称
      - node: 当前节点的详细信息（若存在）
      - error: 失败时的原因
    """

    base = f"http://{host}:{port}"
    headers = {
        "Authorization": f"Bearer {secret}",
        "Accept": "application/json",
    }

    def _get(path: str):
        req = urllib.request.Request(base + path, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                return json.loads(data.decode("utf-8"))
        except Exception:
            return None

    proxies_json = _get("/proxies")
    if not isinstance(proxies_json, dict):
        return {
            "ok": False,
            "group": None,
            "now": None,
            "node": {},
            "error": "无法获取 /proxies 响应，请检查 external-controller 与 secret",
        }

    proxies_dict = proxies_json.get("proxies", proxies_json) or {}

    candidate_groups = [
        "GLOBAL",
        "Proxy",
        "PROXY",
        "🔰 节点选择",
        "节点选择",
        "♻ 自动选择",
    ]

    group_name = None
    now_name = None

    # 先按常见组名查找
    for name in candidate_groups:
        info = proxies_dict.get(name)
        if isinstance(info, dict) and ("now" in info or "history" in info):
            group_name = name
            now_name = info.get("now")
            if not now_name:
                hist = info.get("history") or []
                if hist and isinstance(hist, list):
                    now_name = hist[-1].get("now") or hist[-1].get("name")
            break

    # 若常见组未找到，回退到任意选择/测试组
    if not now_name:
        for name, info in proxies_dict.items():
            if not isinstance(info, dict):
                continue
            if info.get("type") in {"Selector", "URLTest", "Fallback", "LoadBalance"}:
                group_name = name
                now_name = info.get("now")
                if not now_name:
                    hist = info.get("history") or []
                    if hist and isinstance(hist, list):
                        now_name = hist[-1].get("now") or hist[-1].get("name")
                if now_name:
                    break

    node_info = {}
    if now_name and isinstance(proxies_dict.get(now_name), dict):
        node_info = proxies_dict[now_name]

    return {
        "ok": bool(now_name),
        "group": group_name,
        "now": now_name,
        "node": node_info,
        "error": None if now_name else "未找到当前节点，请检查模式或组配置",
    }


def list_nodes_name_delay(
    host: str = "127.0.0.1",
    port: int = 9097,
    secret: str = "abc123456",
    timeout: float = 5.0,
):
    """
    返回所有叶子节点的精简信息：[{"name": ..., "delay": ...}]

    delay 优先使用节点上的 delay 字段；若没有，则尝试从 history 最后一条的 delay。
    """
    data = get_all_clash_verge_nodes(host=host, port=port, secret=secret, timeout=timeout)
    nodes = data.get("nodes", [])
    simple = []
    for n in nodes:
        name = n.get("name")
        delay = n.get("delay")
        if delay is None:
            hist = n.get("history") or []
            if hist and isinstance(hist, list):
                # 尝试使用最后一次测试的延迟
                last = hist[-1]
                delay = last.get("delay")
        simple.append({"name": name, "delay": delay})
    return simple


def get_current_node_name_delay(
    host: str = "127.0.0.1",
    port: int = 9097,
    secret: str = "abc123456",
    timeout: float = 5.0,
):
    """
    返回当前所选节点的精简信息：{"name": ..., "delay": ...}

    delay 优先使用节点上的 delay 字段；若没有，则尝试从 history 最后一条的 delay。
    """
    info = get_current_connected_node(host=host, port=port, secret=secret, timeout=timeout)
    name = info.get("now")
    node = info.get("node") or {}
    delay = node.get("delay")
    if delay is None:
        hist = node.get("history") or []
        if hist and isinstance(hist, list):
            last = hist[-1]
            delay = last.get("delay")
    return {"name": name, "delay": delay}


def get_one_proxy():
    url = "https://white.novproxy.com/white/api?region=US&num=1&time=10&format=1&type=txt"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = resp.read()
            s = data.decode("utf-8").strip()
            try:
                json.loads(s)
                return None
            except Exception:
                pass
            if re.match(r"^[A-Za-z0-9\.-]+:\d{2,5}$", s):
                return s
            return None
    except Exception:
        return None




__all__ = [
    "get_all_clash_verge_nodes",
    "get_current_connected_node",
    "list_nodes_name_delay",
    "get_current_node_name_delay",
]


if __name__ == "__main__":
    print(get_one_proxy())
