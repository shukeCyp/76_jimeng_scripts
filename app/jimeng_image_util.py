import asyncio
import sys
import json
import time
from playwright.async_api import async_playwright

async def generate_image(cookies, username, password, prompt, image_path, headless=True, account_id=None):
    """
    使用Playwright和已登录的session ID生成图片
    :param cookies: cookies列表
    :param username: 用户名
    :param password: 密码
    :param prompt: 提示词
    :param image_path: 图片路径
    :param headless: 是否使用无头模式
    :param account_id: 账号ID，用于保存cookies到数据库
    """
    print(f"开始生成图片，提示词: {prompt}")
    
    async with async_playwright() as p:
        # 启动浏览器
        print("启动浏览器...")
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        print("浏览器启动成功")
        
        # 初始化监听器变量
        task_id = None
        image_urls = []
        generation_completed = False
        
        # 设置响应监听器
        async def handle_response(response):
            nonlocal task_id, image_urls, generation_completed
            
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
                                if "image" in asset and asset["image"].get("finish_time", 0) != 0:
                                    try:
                                        image_urls = []
                                        for i in range(4):
                                            try:
                                                url = asset["image"]["item_list"][i]["image"]["large_images"][0]["image_url"]
                                                image_urls.append(url)
                                            except (KeyError, IndexError):
                                                print(f"无法获取第{i+1}张图片URL")
                                        
                                        if image_urls:
                                            print(f"图片生成完成，共{len(image_urls)}张图片")
                                            for i, url in enumerate(image_urls):
                                                print(f"图片{i+1} URL: {url}")
                                            generation_completed = True
                                        else:
                                            print("图片已完成但无法获取任何URL")
                                            generation_completed = True  # 标记为完成，即使没有URL
                                    except (KeyError, IndexError):
                                        print("图片已完成但无法获取URL")
                                        generation_completed = True  # 标记为完成，即使没有URL
                                else:
                                    print("图片生成尚未完成，继续等待")
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
                await page.wait_for_selector("[class*='credit-display-container']", timeout=30000)
                print("登录成功")
            # 跳转https://dreamina.capcut.com/ai-tool/generate?type=image
            print("跳转到图片生成页面...")
            await page.goto("https://dreamina.capcut.com/ai-tool/generate?type=image", timeout=30000)
            print("图片生成页面加载完成")

            # <button class="lv-btn lv-btn-secondary lv-btn-size-default lv-btn-shape-square button-oBBmQ2" type="button"><svg width="1em" height="1em" viewBox="0 0 24 24" preserveAspectRatio="xMidYMid meet" fill="none" role="presentation" xmlns="http://www.w3.org/2000/svg" class=""><g><path data-follow-fill="currentColor" d="M19.25 17.25V6.75a2 2 0 0 0-2-2H6.75a2 2 0 0 0-2 2v10.5a2 2 0 0 0 2 2h10.5a2 2 0 0 0 2-2Zm2-10.5a4 4 0 0 0-4-4H6.75a4 4 0 0 0-4 4v10.5a4 4 0 0 0 4 4h10.5a4 4 0 0 0 4-4V6.75Z" clip-rule="evenodd" fill-rule="evenodd" fill="currentColor"></path></g></svg><span class="button-text-H4VSVJ">1:1<div class="divider-ys3wAF"></div><div class="commercial-content-ha0tzp">High (2K)</div></span></button>
            # 点击这个
            print("点击1:1比例按钮...")
            await page.click("button:has-text('1:1')")
            print("1:1比例按钮点击完成")


            # 点击第8个单选按钮（使用更稳定的选择器，避免随机类名）
            print("点击第8个单选按钮...")
            await page.wait_for_selector("div.lv-radio-group label.lv-radio:nth-child(9)")
            await page.click("div.lv-radio-group label.lv-radio:nth-child(9)")
            await asyncio.sleep(1)
            print("第8个单选按钮点击完成")
          

            # 点击4K分辨率选项 - 使用JavaScript强制点击匹配文本的元素

            # 点击4K分辨率选项 - 使用更稳定的选择器并结合文本内容定位
            print("点击4K分辨率选项...")
            await page.wait_for_selector("label.lv-radio")
            clicked = await page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label.lv-radio'));
                const targetLabel = labels.find(label => 
                    label.textContent && label.textContent.includes('Ultra (4K)')
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
            print("4K分辨率选项点击完成")

            print("点击9:16比例按钮...")
            await page.click("button:has-text('9:16')")
            print("9:16比例按钮点击完成")

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
            image_urls = []
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
            
            # 等待图片生成完成，最多等待5分钟
            print("等待图片生成完成...")
            start_time = time.time()
            wait_count = 0
            while not generation_completed and (time.time() - start_time) < 300:  # 5分钟超时
                wait_count += 1
                # 如果已获取到任务ID，每5秒刷新一次页面
                if task_id:
                    print(f"已获取任务ID: {task_id}，每5秒刷新一次页面... (等待次数: {wait_count})")
                    await asyncio.sleep(5)
                    print("刷新页面...")
                    await page.reload()
                    print("页面刷新完成")
                else:
                    print(f"尚未获取任务ID，继续等待... (等待次数: {wait_count})")
                    await asyncio.sleep(2)
            
            if generation_completed:
                print("图片生成完成")
                if image_urls:
                    print(f"成功获取{len(image_urls)}张图片URL")
                    for i, url in enumerate(image_urls):
                        print(f"图片{i+1}: {url}")
                else:
                    print("未获取到图片URL，但任务已完成")
            else:
                print("图片生成超时")
          
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
            
            return {"success": True, "cookies": cookies, "image_urls": image_urls}
                
        except Exception as e:
            print(f"图片生成失败: {str(e)}")
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