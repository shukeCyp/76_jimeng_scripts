import asyncio
import sys
import json
import time
import threading
from playwright.async_api import async_playwright
import requests
from proxy_manager import get_one_proxy

async def gen_video_from_images(
    username,
    password,
    image_path,
    prompt_text,
    headless=False
    ):
    """
    从指定目录中的图像生成视频。

    :param image_path: 要上传的图像文件路径。
    :param prompt_text: 用于生成视频的提示词。
    :param headless: 是否以无头模式运行浏览器。
    """
    # 仅接口请求走代理，页面资源等不走代理
    proxy = get_one_proxy()

    print(f"当前代理: {proxy}")
    # 当代理为 None 或空字符串时，不传入 proxy 参数
    launch_kwargs = {
        "headless": False,
        "args": [
            "--start-maximized"
        ]
    }
    if proxy:
        # 同时支持 http 和 https 代
        # launch_kwargs["proxy"] = {"server": f"http://{proxy}"}
        pass

    async with async_playwright() as p:
        # 启动浏览器，非接口流量直连
        print("启动浏览器...")
        browser = await p.chromium.launch(**launch_kwargs)
        # 页面浏览使用无代理上下文
        page_context = await browser.new_context(no_viewport=True)
        # 后续所有页面操作使用 page_context
        page = await page_context.new_page()
        # 直接写入 localStorage，用于关闭引导弹窗，不等待页面加载完毕
        await page.goto("https://app.klingai.com/global/image-to-video/frame-mode/new?ra=4", wait_until="domcontentloaded")
        
        ts1 = int(time.time() * 1000)
        ts2 = ts1 + 1
        await page.evaluate(f"""
            if (window.localStorage) {{
                localStorage.setItem('overlay-manage__guide__image-to-video-by-frame', '{ts1}');
                localStorage.setItem('overlay-manage__guide__digital-human', '{ts2}');
            }}
        """)
        print(f"已向 localStorage 写入时间戳: {ts1}, {ts2}")

        # 初始化监听器变量
        task_id = None
        video_url = None
        generation_completed = False
        # 设置响应监听器
        async def handle_response(response):
            nonlocal task_id, video_url, generation_completed
            if "api/task/submit" in response.url:
                try:
                    data = await response.json()
                    print("[监听器] 监测到生成请求响应")
                    # 优先使用新的 task.id 字段
                    if data.get("ret") == "0" and "data" in data:
                        if "task" in data["data"] and "id" in data["data"]["task"]:
                            task_id = data["data"]["task"]["id"]
                            print(f"[监听器] 获取到任务ID: {task_id}")
                        # 兼容旧字段 aigc_data.task.task_id
                        elif "aigc_data" in data["data"] and "task" in data["data"]["aigc_data"]:
                            task_id = data["data"]["aigc_data"]["task"]["task_id"]
                            print(f"[监听器] 获取到任务ID: {task_id}")
                except Exception as e:
                    print(f"[监听器] 解析 api/task/submit 响应失败: {e}")
            
            if "api/user/works/personal/feeds" in response.url and task_id:
                try:
                    data = await response.json()
                    print("[监听器] 监测到个人作品 feeds 响应")
                    # 优先判断 history 列表
                    history = data.get("data", {}).get("history", [])
                    print(f"[监听器] history 列表长度: {len(history)}")
                    for item in history:
                        works = item.get("works", [])
                        for asset in works:
                            print(f"[监听器] 检查 asset taskId: {asset.get('taskId')} vs 本地 task_id: {task_id}")
                            if asset.get("taskId") == task_id:
                                status = asset.get("status")
                                print(f"[监听器] 匹配到任务，status={status}")
                                # 99 表示完成
                                if status == 99:
                                    resource_url = asset.get("resource", {}).get("resource", "")
                                    if resource_url:
                                        video_url = resource_url
                                        print(f"[监听器] 视频生成完成: {video_url}")
                                    else:
                                        print("[监听器] 视频已完成但 resource 为空")
                                    generation_completed = True
                                    return
                                # 10 表示失败
                                elif status == 10:
                                    print("[监听器] 视频生成失败，任务异常")
                                    generation_completed = True
                                    return
                                else:
                                    print(f"[监听器] 视频生成尚未完成，status={status}，继续等待")
                                    return
                except Exception as e:
                    print(f"[监听器] 解析 api/user/works/personal/feeds 响应失败: {e}")
        
        # 注册响应监听器
        page.on("response", handle_response)
        print("已注册响应监听器")

        print("浏览器启动成功，窗口已全屏")
        await page.goto("https://app.klingai.com/global/image-to-video/frame-mode/new?ra=4", timeout=60000)
        print("已跳转至首页")

        # 点击“Sign In”按钮
        print("等待 Sign In 按钮...")
        sign_in_btn = await page.wait_for_selector('div.user-profile-link.all-center:has-text("Sign In")', timeout=10000)
        await sign_in_btn.click()
        print("已点击 Sign In")

        # 点击“Sign in with email”按钮
        print("等待 Sign in with email 按钮...")
        email_sign_in_btn = await page.wait_for_selector('div.sign-in-button:has-text("Sign in with email")', timeout=10000)
        await email_sign_in_btn.click()
        print("已点击 Sign in with email")

        # 输入邮箱
        print("等待邮箱输入框...")
        email_input = await page.wait_for_selector('input[placeholder="Email"]', timeout=10000)
        await email_input.fill(username)
        print("已输入邮箱")

        # 输入密码
        print("等待密码输入框...")
        pwd_input = await page.wait_for_selector('input[placeholder="Password"]', timeout=10000)
        await pwd_input.fill(password)
        print("已输入密码")

        # 点击登录按钮
        print("等待登录按钮...")
        login_btn = await page.wait_for_selector('button.generic-button.critical.large:has-text("Sign In")', timeout=10000)
        await login_btn.click()
        print("已点击登录按钮")
        # 等待登录完成并跳转到 image-to-video 页面
        await page.wait_for_load_state("networkidle")
        
        print("已跳转到 image-to-video 页面")
        
        # 短暂等待页面稳定
        print("等待页面稳定 2 秒...")
        await asyncio.sleep(2)

        # 统一使用 JS 方式上传，兼容旧版和新版 input
        print(f"读取图片文件: {image_path}")
        with open(image_path, "rb") as f:
            file_buffer = f.read()
        print(f"读取图片完成，大小: {len(file_buffer)} 字节")
        file_name = image_path.split(r'[\\/]').pop()
        print(f"准备上传文件: {file_name}")
        await page.evaluate(
            """([buffer, name]) => {
                const inputs = document.querySelectorAll('input[type="file"][accept=".jpg,.jpeg,.png"]');
                if (inputs.length === 0) throw new Error('未找到上传 input');
                const dt = new DataTransfer();
                const file = new File([new Uint8Array(buffer)], name, { type: 'image/jpeg' });
                dt.items.add(file);
                inputs[0].files = dt.files;
                inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            [file_buffer, file_name]
        )
        print(f"已使用 JS 方式上传图片: {image_path}")

        print("等待上传后 5 秒...")
        await asyncio.sleep(5)

        # 等待图片上传完成并出现提示词输入框
        print("等待提示词输入框出现...")

        # js执行document.querySelector('div.tiptap.ProseMirror[contenteditable="true"]').innerHTML = '12345';
        print("填充提示词到输入框...")
        await page.evaluate(f"document.querySelector('div.tiptap.ProseMirror[contenteditable=\"true\"]').innerHTML = '{prompt_text}';")
        print("提示词填充完成")

        await asyncio.sleep(2)

        # 点击 Generate 按钮
        print("等待 Generate 按钮...")
        generate_btn = await page.wait_for_selector(
            'button.generic-button.critical.big:has-text("Generate")',
            timeout=10000
        )
        await generate_btn.click()
        print("已点击 Generate 按钮，开始生成视频")

        # 等待 task_id，最多60次，每次1秒
        print("等待 task_id 中...")
        for i in range(60):
            if task_id is not None:
                print(f"成功获取 task_id: {task_id} (耗时 {i+1} 秒)")
                break
            await asyncio.sleep(1)
        else:
            print("未能在60秒内获取到任务ID，退出")
            await browser.close()
            return

        # 循环判断是否完成，5秒一次，最多60次
        print("等待视频生成完成...")
        for i in range(60):
            if generation_completed:
                print(f"视频生成完成或失败 (耗时 {(i+1)*5} 秒)")
                break
            print(f"第 {i+1} 次轮询，继续等待...")
            await asyncio.sleep(5)
        else:
            print("未能在300秒内完成视频生成，退出")

        # 输出视频链接
        if video_url:
            print(f"最终视频链接: {video_url}")
        else:
            print("未能获取到视频链接")

        # 关闭浏览器
        await browser.close()
        print("浏览器已关闭")


def main():
    print("主函数开始")
    asyncio.run(gen_video_from_images(
        username="JustinPerez7019@hotmail.com",
        password="nuhhvneu61490",
        image_path="c:\\Users\\35368\\Desktop\\d4d9cd1b71568fd8fb798abd8f9eee6c.jpg",
        prompt_text="A beautiful sunset over the mountains"
    ))
    print("主函数结束")


if __name__ == "__main__":
    main()
