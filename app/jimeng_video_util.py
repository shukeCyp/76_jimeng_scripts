import asyncio
import sys
import json
import time
from unittest import result
from playwright.async_api import async_playwright

async def generate_video(
    cookies, 
    username, 
    password, 
    prompt, 
    seconds,
    image_path, 
    headless=True,
    account_id=None):
    """
    使用Playwright和已登录的session ID生成视频
    :param cookies: cookies列表
    :param username: 用户名
    :param password: 密码
    :param prompt: 提示词
    :param seconds: 视频时长（秒）
    :param image_path: 图片路径
    :param headless: 是否使用无头模式
    :param account_id: 账号ID，用于保存cookies到数据库
    """
    print(f"开始生成视频，提示词: {prompt}")
    
    async with async_playwright() as p:
        # 启动浏览器
        print("启动浏览器...")
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        print("浏览器启动成功")
        
        # 初始化监听器变量
        task_id = None
        video_url = None
        generation_completed = False
        
        # 设置响应监听器
        async def handle_response(response):
            nonlocal task_id, video_url, generation_completed
            
            if "aigc_draft/generate" in response.url:
                try:
                    data = await response.json()
                    print("监测到生成请求响应")
                    if data.get("ret") == "0" and "data" in data and "aigc_data" in data["data"]:
                        task_id = data["data"]["aigc_data"]["task"]["task_id"]
                        print(f"获取到任务ID: {task_id}")
                except:
                    pass
            
            if "/v1/get_asset_list" in response.url and task_id:
                try:
                    data = await response.json()
                    if "data" in data and "asset_list" in data["data"]:
                        asset_list = data["data"]["asset_list"]
                        for asset in asset_list:
                            if "id" in asset and asset.get("id") == task_id:
                                # 检查视频生成是否完成
                                if "video" in asset and asset["video"].get("finish_time", 0) != 0:
                                    try:
                                        # 获取视频URL
                                        if "item_list" in asset["video"] and len(asset["video"]["item_list"]) > 0:
                                            video_item = asset["video"]["item_list"][0]
                                            if "video" in video_item and "transcoded_video" in video_item["video"]:
                                                transcoded = video_item["video"]["transcoded_video"]
                                                if "origin" in transcoded and "video_url" in transcoded["origin"]:
                                                    video_url = transcoded["origin"]["video_url"]
                                        
                                        if video_url:
                                            print(f"视频生成完成: {video_url}")
                                            generation_completed = True
                                        else:
                                            print("视频已完成但无法获取URL")
                                            generation_completed = True  # 标记为完成，即使没有URL
                                    except (KeyError, IndexError):
                                        print("视频已完成但无法获取URL")
                                        generation_completed = True  # 标记为完成，即使没有URL
                                else:
                                    print("视频生成尚未完成，继续等待")
                except:
                    pass
        
        # 注册响应监听器
        page.on("response", handle_response)
        

        try:
            if cookies:
                await page.context.add_cookies(cookies)
            # 访问登录页面
            print("访问登录页面...")
            await page.goto("https://dreamina.capcut.com/ai-tool/login", timeout=60000)
            print("登录页面加载完成")
            try:
                await page.wait_for_selector("img.dreamina-component-avatar", timeout=30000)
            except Exception:
                # <div class="lv-checkbox-mask lv-checkbox-mask"><svg class="lv-checkbox-mask-icon lv-checkbox-mask-icon" aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M18.8536 8.35355C19.0489 8.54882 19.0489 8.8654 18.8536 9.06066L10.8536 17.0607C10.6584 17.2559 10.3418 17.2559 10.1465 17.0607L5.14651 12.0607C4.95125 11.8654 4.95125 11.5488 5.14651 11.3536L5.85361 10.6464C6.04888 10.4512 6.36546 10.4512 6.56072 10.6464L10.5001 14.5858L17.4394 7.64645C17.6347 7.45118 17.9512 7.45118 18.1465 7.64645L18.8536 8.35355Z" p-id="840"></path></svg></div>
                # 勾选这个
                print("开始执行登录操作")
                print("勾选协议...")
                await page.click("[class*='lv-checkbox-mask']")
                print("协议勾选完成")

                # 点击登录按钮 (使用更稳定的定位方式)
                print("点击登录按钮...")
                await page.wait_for_selector("[class*='login-button']")
                await page.click("[class*='login-button']")
                print("登录按钮点击完成")
                
                # 点击邮箱登录选项（通过文字匹配）
                print("选择邮箱登录...")
                await page.wait_for_selector("span:has-text('Continue with email')")
                await page.click("span:has-text('Continue with email')")
                print("邮箱登录选项点击完成")
                
                
                # 输入邮箱
                print("输入邮箱...")
                await page.wait_for_selector("input[placeholder='Enter email']")
                await page.fill("input[placeholder='Enter email']", username)
                print("邮箱输入完成")
                
                # 输入密码
                print("输入密码...")
                await page.wait_for_selector("input[type='password']")
                await page.fill("input[type='password']", password)
                print("密码输入完成")
                
                # 点击登录按钮
                print("点击继续登录...")
                await page.click("button:has-text('Continue')")
                print("登录按钮点击完成")
                
                # 等待登录成功的标识元素出现 (使用更稳定的定位方式)
                # 等待包含积分显示的容器出现，表示登录成功
                print("等待登录成功...")
                await page.wait_for_selector("[class*='credit-display-container']", timeout=60000)
                print("登录成功")
            # 跳转https://dreamina.capcut.com/ai-tool/generate?type=video
            print("跳转到视频生成页面...")
            await page.goto("https://dreamina.capcut.com/ai-tool/generate?type=video", timeout=60000)
            print("视频生成页面加载完成")

            # <button class="lv-btn lv-btn-secondary lv-btn-size-default lv-btn-shape-square button-oBBmQ2" type="button"><svg width="1em" height="1em" viewBox="0 0 24 24" preserveAspectRatio="xMidYMid meet" fill="none" role="presentation" xmlns="http://www.w3.org/2000/svg" class=""><g><path data-follow-fill="currentColor" d="M19.25 17.25V6.75a2 2 0 0 0-2-2H6.75a2 2 0 0 0-2 2v10.5a2 2 0 0 0 2 2h10.5a2 2 0 0 0 2-2Zm2-10.5a4 4 0 0 0-4-4H6.75a4 4 0 0 0-4 4v10.5a4 4 0 0 0 4 4h10.5a4 4 0 0 0 4-4V6.75Z" clip-rule="evenodd" fill-rule="evenodd" fill="currentColor"></path></g></svg><span class="button-text-H4VSVJ">1:1<div class="divider-ys3wAF"></div><div class="commercial-content-ha0tzp">High (2K)</div></span></button>
            # 点击这个
            print("点击1:1比例按钮...")
            await page.click("button:has-text('16:9')")
            print("9:16比例按钮点击完成")


            # 点击1080P分辨率选项 - 使用更稳定的选择器并结合文本内容定位

            print("点击1080P分辨率选项...")
            await page.wait_for_selector("label.lv-radio")
            clicked = await page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label.lv-radio'));
                const targetLabel = labels.find(label => 
                    label.textContent && label.textContent.includes('1080P')
                );
                if (targetLabel) {
                    // 滚动到元素可见位置
                    targetLabel.scrollIntoViewIfNeeded();
                    // 添加短暂延迟确保渲染完成
                    setTimeout(() => {
                        targetLabel.click();
                    }, 100);
                    return true;
                }
                return false;
            }''')
            # 等待点击后的状态变化（可选，根据实际页面行为调整）
            await asyncio.sleep(1)
            print("1080P分辨率选项点击完成")

            # 点击4K分辨率选项 - 使用JavaScript强制点击匹配文本的元素

            print("点击9:16比例按钮...")
            await page.click("button:has-text('16:9')")
            print("9:16比例按钮点击完成")

            # <span class="lv-select-view-value"><span class="select-option-icon-c5Ol2F"><svg width="1em" height="1em" viewBox="0 0 24 24" preserveAspectRatio="xMidYMid meet" fill="none" role="presentation" xmlns="http://www.w3.org/2000/svg" class=""><g><path data-follow-fill="currentColor" d="M4 12a8 8 0 1 0 16 0 8 8 0 0 0-16 0Zm8 10C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10Zm-.866-10.5a1 1 0 1 0 1.732 1l2-3.464a1 1 0 1 0-1.732-1l-2 3.464Z" clip-rule="evenodd" fill-rule="evenodd" fill="currentColor"></path></g></svg></span>5s</span>
            # 点击选择时长
            print("点击选择时长...")
            # 先等待包含“5s”文本的下拉按钮出现
            await page.wait_for_selector('span.lv-select-view-value:has-text("5s")', timeout=10000)
            # 使用更稳定的 JS 强制点击
            clicked = await page.evaluate('''() => {
                const span = document.querySelector('span.lv-select-view-value');
                if (span) {
                    span.scrollIntoView({behavior: "instant", block: "center"});
                    // 强制触发点击
                    span.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    span.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                    span.click();
                    return true;
                }
                return false;
            }''')
            if not clicked:
                # 兜底：直接点击包含“5s”文本的 span
                await page.click('span.lv-select-view-value:has-text("5s")')
            print("选择时长点击完成")
            # 根据传入的 seconds 参数选择对应时长
            duration_text = f"{seconds}s"
            print(f"选择时长: {duration_text}")
            # 先点击下拉展开时长选项
            await page.click("span:has-text('5s')")
            # 点击目标时长选项
            await page.click(f"li[role='option']:has-text('{duration_text}')")
            print("目标时长选择完成")

            # 使用js强制点击

            # 查找文件上传输入框
            print("查找文件上传输入框...")
            upload_selector = 'input[type="file"][accept*="image"]'
            await page.wait_for_selector(upload_selector, timeout=10000, state='attached')
            print("文件上传输入框找到")
                    
            # 上传图片文件
            print(f"上传图片文件: {image_path}")
            await page.set_input_files(upload_selector, image_path)
            print("图片文件上传完成")

            # 输入提示词 (使用更稳定的选择器，避免随机类名)
            print("输入提示词...")
            await page.wait_for_selector("textarea")
            await page.fill("textarea", prompt)
            print("提示词输入完成")



            # 使用更稳定的选择器并强制点击提交按钮

            time.sleep(3)
            print("点击提交按钮...")
            # 等待提交按钮可点击
            
            # 重置状态变量
            print("重置任务状态变量...")
            task_id = None
            video_url = None
            generation_completed = False
            print("任务状态变量重置完成")
            
            # 尝试多种方式点击按钮
            print("开始尝试点击提交按钮...")
            # 方法1: 使用evaluate执行点击
            print("尝试方法1: 使用evaluate执行点击...")
            clicked = await page.evaluate('''() => {
                const button = document.querySelector('button[class*="submit-button-"]:not(.lv-btn-disabled)');
                if (button) {
                    button.scrollIntoViewIfNeeded();
                    button.click();
                    console.log("方法1点击完成");
                    return true;
                }
                console.log("方法1未找到按钮");
                return false;
            }''')
            print(f"方法1执行结果: {clicked}")
            
            # 如果方法1失败，尝试方法2: 直接使用click
            if not clicked:
                print("方法1失败，尝试方法2: 直接使用click...")
                try:
                    await page.click('button[class*="submit-button-"]:not(.lv-btn-disabled)', timeout=5000)
                    clicked = True
                    print("方法2点击成功")
                except Exception as click_error:
                    print(f"方法2点击失败: {str(click_error)}")
                    pass
            
            # 如果方法2失败，尝试方法3: 使用dispatchEvent
            if not clicked:
                print("方法2失败，尝试方法3: 使用dispatchEvent...")
                result = await page.evaluate('''() => {
                    const button = document.querySelector('button[class*="submit-button-"]:not(.lv-btn-disabled)');
                    if (button) {
                        button.scrollIntoViewIfNeeded();
                        const event = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        const success = button.dispatchEvent(event);
                        console.log("方法3执行完成，dispatchEvent结果: " + success);
                        return success;
                    }
                    console.log("方法3未找到按钮");
                    return false;
                }''')
                print(f"方法3执行结果: {result}")
            
            print("提交按钮点击流程完成")
            
            # 等待视频生成完成，最多等待15分钟；等待任务ID最多60次
            print("等待视频生成完成...")
            start_time = time.time()
            wait_count = 0
            max_wait_without_taskid = 60
            no_taskid_attempts = 0
            taskid_wait_exceeded = False
            while not generation_completed and (time.time() - start_time) < 900:  # 15分钟超时
                wait_count += 1
                # 如果已获取到任务ID，每5秒刷新一次页面
                if task_id:
                    print(f"已获取任务ID: {task_id}，每5秒刷新一次页面... (等待次数: {wait_count})")
                    await asyncio.sleep(5)
                    print("刷新页面...")
                    await page.reload()
                    print("页面刷新完成")
                else:
                    no_taskid_attempts += 1
                    print(f"尚未获取任务ID，继续等待... (等待次数: {wait_count}，未获ID计数: {no_taskid_attempts}/{max_wait_without_taskid})")
                    await asyncio.sleep(2)
                    if no_taskid_attempts >= max_wait_without_taskid:
                        print(f"超过最大等待次数({max_wait_without_taskid})，未获取到任务ID")
                        taskid_wait_exceeded = True
                        break
            
            if generation_completed:
                print("视频生成完成")
                if video_url:
                    print(f"成功获取视频URL: {video_url}")
                else:
                    print("未获取到视频URL，但任务已完成")
            else:
                print("视频生成超时")
          
            # 获取并返回cookies
            cookies = await page.context.cookies()
            print("获取cookies完成")

            # 如果有账号ID，保存cookies到数据库
            if account_id and cookies:
                try:
                    # 导入更新cookies的函数
                    from accounts_utils import update_account_cookies
                    # 更新账号的cookies
                    if update_account_cookies(account_id, cookies):
                        print(f"账号 {account_id} 的cookies已保存到数据库")
                    else:
                        print(f"保存账号 {account_id} 的cookies到数据库失败")
                except Exception as e:
                    print(f"保存cookies到数据库时出错: {e}")

            # 根据等待结果返回成功或失败
            if generation_completed:
                return {"success": True, "cookies": cookies, "video_url": video_url}
            else:
                err_msg = "等待任务ID超过最大次数(60)" if taskid_wait_exceeded else "视频生成超时"
                return {"success": False, "error": err_msg, "cookies": cookies}
                
        except Exception as e:
            print(f"视频生成失败: {str(e)}")
            # 即使失败也尝试获取cookies
            try:
                cookies = await page.context.cookies()
                print("获取cookies完成")
                
                # 如果有账号ID，保存cookies到数据库
                if account_id and cookies:
                    try:
                        # 导入更新cookies的函数
                        from accounts_utils import update_account_cookies
                        # 更新账号的cookies
                        if update_account_cookies(account_id, cookies):
                            print(f"账号 {account_id} 的cookies已保存到数据库")
                        else:
                            print(f"保存账号 {account_id} 的cookies到数据库失败")
                    except Exception as save_error:
                        print(f"保存cookies到数据库时出错: {save_error}")
                
                return {"success": False, "error": str(e), "cookies": cookies}
            except Exception as cookie_error:
                print(f"获取cookies失败: {cookie_error}")
                return {"success": False, "error": str(e)}
        finally:
            print("关闭浏览器...")
            await browser.close()
            print("浏览器已关闭")
async def main():
    """
    命令行入口：读取参数并调用 generate_video
    参数顺序：
        1. username      邮箱账号
        2. password      密码
        3. prompt        提示词（如有空格请用引号包裹）
        4. seconds       视频时长（秒）
        5. image_path    图片绝对路径
        6. headless      可选，默认 true；传 false 可开启有头模式
        7. account_id    可选，账号ID，用于保存 cookies 到数据库
    示例：
        python jimeng_video_util.py user@example.com 123456 "a cute cat" 10 /tmp/cat.png
    """
    # 参数写死
    username   = "gaqkqgscn@emltmp.com"
    password   = "Aa123456"
    prompt     = "跳舞"
    seconds    = 10
    image_path = "/Users/chaiyapeng/Downloads/17311948576731018310.webp"
    headless   = False
    account_id = None

    # 空 cookies 列表，首次登录
    cookies = [{"name": "cee", "value": "JdLcaXDeh57HIdKMfCgEdwcO2Slz3Za3JJw8miqXkLI%3D.%7B%7D", "domain": ".mpc-prod-18-s6uit34pua-uc.a.run.app", "path": "/events/8fb2ad23c8f8b94190406835a6eae1e6345627ad967b4a2e640ff3fb88fec43c", "expires": 1770140167.969067, "httpOnly": True, "secure": True, "sameSite": "None"}, {"name": "faceu-commerce-user-info", "value": "Z0zKU04UXS5AFeUs2R5BPcv-C5S2ojPaouDN90apvkmcPzwgDgPfJ9UJRpbIRojlxW_4hlKZj6nTiGOzA4OmlnlQcboCdWLkSInCMZmEkasnUlGxd9W8MtYj3n2ZfGEHWzrahyE3jpVpCQ_yZQEVoxlSH3JK0LYa-Sn6VyW6WWuiCQXAa6-i8kVhYxk1jRhdIlxLrW8SqFsrugqeFs2kuoQFIVBD0dGilp96fEYu3uLOpTJClv5QeHtiBwYskMzh-H1BytZkIvAAdaxmpSblQeZJo_3qxQ6KUdAsEbgAu8T6lgbbf19YM7wBv1HNaiZKg4ShDCZzdSwLp7RuE2ir8AUlrwW3L7rdpMmQaTuzVT7OvEIIc8rWbppV4sMmhkEOI-VDD4pXp65T_fToR5KiCOUAtwkBv0-NCFZuu1Et3Fam5DHkYYy70_xyGhiLOS-ZT_cb-5a5GWqyBSIjjBK7cuIx3GkpWcRxpz9PNoT8ux9uo-_Ju6Kb7UKBaACCuMfEHgO7Nk2hjlg6MBBjGXD4", "domain": ".capcut.com", "path": "/commerce/v1/subscription/user_info", "expires": 1796924160.939075, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "_tea_web_id", "value": "7569211615418172944", "domain": "dreamina.capcut.com", "path": "/", "expires": 1762497099.594887, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "capcut_locale", "value": "en", "domain": "dreamina.capcut.com", "path": "/", "expires": 1796472432, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "fpk1", "value": "02303d267268c4525e2b514de13679cd3704b955dd366a574b995db6a80fb3bf34025180dd180393484130abd4d7971b", "domain": "dreamina.capcut.com", "path": "/", "expires": 1793880433.73402, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "uifid_temp", "value": "89e9331e58b9970efe317e494d7d1997271d127b1b4b7326b704a4b07dc10a3b65c828672874a16680395e102a8d819fa2183906812baffbbfaaf7a3d832b8cc391ef377e9a6aad7d0acd5f5d91013f4", "domain": "mweb-api-sg.capcut.com", "path": "/", "expires": 1796904434.160437, "httpOnly": False, "secure": True, "sameSite": "None"}, {"name": "_isCommercialFreemiumStage", "value": "0", "domain": "dreamina.capcut.com", "path": "/", "expires": 1762968961, "httpOnly": False, "secure": True, "sameSite": "Strict"}, {"name": "s_v_web_id", "value": "verify_mhlyeewl_qfpZrlwK_wC9U_4OZW_8i0W_EccFmhc0exaB", "domain": "dreamina.capcut.com", "path": "/", "expires": -1, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "passport_csrf_token", "value": "0bb9d3ab597a231060dd64a7d21c31ec", "domain": ".capcut.com", "path": "/", "expires": 1767528480.809554, "httpOnly": False, "secure": True, "sameSite": "None"}, {"name": "passport_csrf_token_default", "value": "0bb9d3ab597a231060dd64a7d21c31ec", "domain": ".capcut.com", "path": "/", "expires": 1767528480.809586, "httpOnly": False, "secure": True, "sameSite": "Lax"}, {"name": "sid_guard", "value": "8b558ef8e419009774213686eee77abd%7C1762344484%7C5183999%7CSun%2C+04-Jan-2026+12%3A08%3A03+GMT", "domain": ".capcut.com", "path": "/", "expires": 1793448482.069355, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "uid_tt", "value": "d1e27d12f65739eadb12aefb345dcd7f834349d7e4fd9930439a00f68b473349", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069394, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "uid_tt_ss", "value": "d1e27d12f65739eadb12aefb345dcd7f834349d7e4fd9930439a00f68b473349", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069403, "httpOnly": True, "secure": True, "sameSite": "None"}, {"name": "sid_tt", "value": "8b558ef8e419009774213686eee77abd", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069411, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "sessionid", "value": "8b558ef8e419009774213686eee77abd", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069418, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "sessionid_ss", "value": "8b558ef8e419009774213686eee77abd", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069425, "httpOnly": True, "secure": True, "sameSite": "None"}, {"name": "tt_session_tlb_tag", "value": "sttt%7C5%7Ci1WO-OQZAJd0ITaG7ud6vf________-5KuCwWjaQtk6e-2-oOgsjZsWdUrkSlBoEUKH7pOKNAsM%3D", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069434, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "sid_ucp_v1", "value": "1.0.0-KDYzYjFkYTY5NTQyYzVmNjE0MmEzMWU5NDI5Yzc4Mjg3ZTRhMTRlYmMKGQiSiIGIyZaL_mgQpPysyAYY6awfOAFA6wcQAxoDbXkyIiA4YjU1OGVmOGU0MTkwMDk3NzQyMTM2ODZlZWU3N2FiZA", "domain": ".capcut.com", "path": "/", "expires": 1767528481.06944, "httpOnly": True, "secure": True, "sameSite": "Lax"}, {"name": "ssid_ucp_v1", "value": "1.0.0-KDYzYjFkYTY5NTQyYzVmNjE0MmEzMWU5NDI5Yzc4Mjg3ZTRhMTRlYmMKGQiSiIGIyZaL_mgQpPysyAYY6awfOAFA6wcQAxoDbXkyIiA4YjU1OGVmOGU0MTkwMDk3NzQyMTM2ODZlZWU3N2FiZA", "domain": ".capcut.com", "path": "/", "expires": 1767528481.069449, "httpOnly": True, "secure": True, "sameSite": "None"}, {"name": "store-idc", "value": "alisg", "domain": ".capcut.com", "path": "/", "expires": 1767528483.916554, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "store-country-code", "value": "cn", "domain": ".capcut.com", "path": "/", "expires": 1767528483.91687, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "store-country-code-src", "value": "uid", "domain": ".capcut.com", "path": "/", "expires": 1767528483.916882, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "cc-target-idc", "value": "alisg", "domain": ".capcut.com", "path": "/", "expires": 1767528483.916893, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "tt-target-idc-sign", "value": "X2BoTwdTNpgu4GjUvO3hYeOYk40el_P7TAqJu44-UpwGU_0Hv65uZ2pj1PtTzb45d5l6FXtuLNda_31JAkAnWP34XrjVzA0q9Vus4sXb_RzpbtQnQfC2s0arql_Ro6B96uqaD8b5U-x4wHJN1Xc08Fxzd3Wm9z5zGKl1ZXYEiORWCBtKJ8-3LKIElt-EhvKOLCdofQvYcBVfsWnk4jCHmj13voGkbWg0zdpPMBX0okWfF_pasPx7WhuniA7xgfeVVC8kDjbWlVCeILECrPNUVBFuBmB_oMDkUD-ZwObpfcQC0nbiDg4P_2rI8O5J0_0AoRKX6TeQNI6MzR29B8sI-2nQcmjkdla7SLEcKPvUa9wGnH5Azv3I4A_LViD9OEBcuSMaF88tswlEVxUNzWqPiniiQA2qzmgYFWagP1AKVYNQyjGUDbWbcIpPFv5ohku6JJDw-O_sDb3VUZSUIDNksNHf1luc2MIsp77CseksmGZfSbG2ObNgDUsxrsTmUYm-", "domain": ".capcut.com", "path": "/", "expires": 1793880482.069502, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "dm_auid", "value": "8wgy8Lwkl0+ju9acj2ogNwGQ1GmaXfaYM/pQFHj82W8=", "domain": "mweb-api-sg.capcut.com", "path": "/", "expires": 1796904484.266345, "httpOnly": False, "secure": True, "sameSite": "None"}, {"name": "_fbp", "value": "fb.1.1762363982720.917256718191619554", "domain": ".capcut.com", "path": "/", "expires": 1770140167, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "_ga", "value": "GA1.1.1025518833.1762363983", "domain": ".capcut.com", "path": "/", "expires": 1796924167.702435, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "store-country-sign", "value": "MEIEDGQNrE0RWF4Zen4lMAQgZB_Nff838HahwKVGgsVhPljjCTPV2yfnzbWlHvDvg0AEEKiKfffPjKE1ApWnqw_3qA4", "domain": ".capcut.com", "path": "/", "expires": 1767528483.916852, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "msToken", "value": "_Ur9qfRa6E1BUVJym9J153j2haNfoBPKZbSGDu9zRCQ937LWGCY_5d9vgeSvCIwIdEkL65UGeQUA1eTm2u1zieyNWJWBT176NtrfkY8_CoiiBg==", "domain": ".capcut.com", "path": "/", "expires": 1763228162.146286, "httpOnly": False, "secure": True, "sameSite": "None"}, {"name": "odin_tt", "value": "17eee1f15203f2b63f921838d9c3075fa84c324eea645d83e8ce5e8f986e255cb4186cbec30007c62df63982fcd13520afce22052f597f414aaac6fdcd260825", "domain": ".capcut.com", "path": "/", "expires": 1793900162.160153, "httpOnly": True, "secure": False, "sameSite": "Lax"}, {"name": "_ga_F8PY8CNX7V", "value": "GS2.1.s1762363983$o1$g1$t1762364167$j14$l0$h0", "domain": ".capcut.com", "path": "/", "expires": 1796924167.709867, "httpOnly": False, "secure": False, "sameSite": "Lax"}, {"name": "ttwid", "value": "1|BLc8-mBixUXj4DwVjEZTALCE4Mo-64qDDLvRCsNyWRk|1762410699|78f4cce877d7f6617a26546184358e617a14b14b3812b3ee6d8c37f07f7b8fe8", "domain": ".capcut.com", "path": "/", "expires": 1793946699.594832, "httpOnly": True, "secure": True, "sameSite": "Lax"}]

    result = await generate_video(
        cookies=cookies,
        username=username,
        password=password,
        prompt=prompt,
        seconds=seconds,
        image_path=image_path,
        headless=headless,
        account_id=account_id
    )

    print("\n===== 执行结果 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
