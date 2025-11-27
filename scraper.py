# scraper.py
import asyncio
import random
from datetime import datetime

async def human_wait(min_seconds=0.3, max_seconds=1.0):
    """模拟人类等待时间"""
    wait_time = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(wait_time)

async def check_and_handle_slider(page):
    """检查并处理滑块验证"""
    try:
        # 检查是否有滑块验证
        slider_selectors = [
            "text=请完成安全验证",
            "text=安全验证",
            "text=验证码",
            ".slider",
            ".captcha",
            ".geetest"
        ]
        
        for selector in slider_selectors:
            if await page.locator(selector).count() > 0:
                print("检测到滑块验证，请人工完成滑块验证...")
                print("请在浏览器中完成滑块验证，完成后回到控制台按回车继续...")
                input("完成后按回车继续...")
                # 给用户足够时间完成滑块
                await human_wait(3, 5)
                print("继续执行...")
                return True
        return False
    except Exception as e:
        print(f"检查滑块验证时出错: {e}")
        return False

async def setup_browser(p):
    """设置浏览器和页面配置"""
    browser = await p.chromium.launch(
        headless=False, 
        slow_mo=100,
        timeout=60000
    )
    
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ignore_https_errors=True
    )
    
    page = await context.new_page()
    
    print("正在打开目标网站...")
    await page.goto("https://xxgs.chinanpo.mca.gov.cn/gsxt/newList", 
                  wait_until="domcontentloaded",
                  timeout=60000)
    print("页面加载成功")
    await human_wait(2, 3)
    
    # 检查初始页面是否有滑块
    await check_and_handle_slider(page)
    
    return browser, page

async def set_filters(page, province, keyword):
    """设置网页筛选条件"""
    print("正在设置筛选条件...")
    
    try:
        # 设置组织状态：正常
        print("设置组织状态：正常")
        normal_status = page.locator("text=正常").first
        await normal_status.click()
        await human_wait(0.5, 1)

        # 设置信用状况：正常
        print("设置信用状况：正常")
        normal_credit = page.locator("text=正常").nth(1)
        await normal_credit.click()
        await human_wait(0.5, 1)

        # 设置组织类型：社会团体
        print("设置组织类型：社会团体")
        social_group = page.locator("text=社会团体").first
        await social_group.click()
        await human_wait(0.5, 1)

        # 输入搜索关键词
        print(f"正在输入搜索关键词: {keyword}")
        search_input = page.locator("input[placeholder='请输入社会组织名称或统一社会信用代码']")
        await search_input.fill(keyword)
        await human_wait(0.5, 1)

        # 点击空白区域关闭可能的下拉菜单
        print("点击空白区域关闭下拉菜单...")
        await page.mouse.click(200, 150)
        await human_wait(0.5, 1)

        # 选择省份
        print(f"正在选择省份: {province}")
        province_dropdown = page.locator(".ant-select-selection").first
        await province_dropdown.click()
        await human_wait(0.5, 1)
        
        # 选择具体的省份选项
        province_option = page.locator(f"text={province}").first
        await province_option.click()
        await human_wait(0.5, 1)

        # 执行搜索 - 关键操作1：点击检索之后检查滑块
        print("正在执行搜索...")
        search_button = page.locator(".search_button").first
        await search_button.click()
        await human_wait(3, 5)

        # 检查搜索后的滑块
        await check_and_handle_slider(page)
            
    except Exception as e:
        print(f"设置筛选条件时出错: {e}")
        raise

async def check_item_validity(page, item_index):
    """检查数据项是否在2025-12-31之前有效"""
    try:
        # 重新获取列表项，防止Stale元素引用
        list_items = page.locator(".list_li")
        item = list_items.nth(item_index)
        
        # 点击标题进入详情页 - 关键操作2：点击详情页面之后检查滑块
        title_element = item.locator(".title_text")
        print(f"  点击标题进入详情页...")
        await title_element.click()
        await human_wait(3, 5)
        
        # 检查详情页加载过程中的滑块
        await check_and_handle_slider(page)
        
        # 等待详情页加载完成
        try:
            await page.wait_for_load_state('networkidle', timeout=15000)
            await human_wait(1, 2)
            
            # 检查是否成功跳转到详情页
            current_url = page.url
            if "detail" in current_url or "newList" not in current_url:
                print(f"  成功跳转到详情页")
            
            # 尝试多种选择器查找有效期信息
            selectors_to_try = [
                ".data_span.text",
                ".data_span", 
                ".text_span",
                ".ant-descriptions-item-content",
                ".ant-card-body"
            ]
            
            validity_text = ""
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    elements = page.locator(selector)
                    count = await elements.count()
                    for i in range(min(count, 10)):
                        element_text = await elements.nth(i).inner_text()
                        element_text_clean = element_text.replace('\n', ' ').strip()
                        if "至" in element_text_clean and ("年" in element_text_clean or "-" in element_text_clean):
                            validity_text = element_text_clean
                            print(f"  找到有效期信息: {validity_text}")
                            break
                    if validity_text:
                        break
                except:
                    continue
            
            # 如果没找到，尝试通用文本搜索
            if not validity_text:
                print("  尝试通用文本搜索有效期信息...")
                page_text = await page.inner_text("body")
                lines = page_text.split('\n')
                for line in lines[:20]:
                    line_clean = line.strip()
                    if "至" in line_clean and ("年" in line_clean or "-" in line_clean):
                        validity_text = line_clean
                        print(f"  从页面文本找到有效期: {validity_text}")
                        break
        
        except Exception as load_error:
            print(f"  详情页加载异常: {load_error}")
            try:
                page_text = await page.inner_text("body")
                if "有效期" in page_text or "至" in page_text:
                    lines = page_text.split('\n')
                    for line in lines[:15]:
                        line_clean = line.strip()
                        if "至" in line_clean and ("年" in line_clean or "-" in line_clean):
                            validity_text = line_clean
                            break
            except:
                pass
        
        # 检查是否在2025-12-31之前有效
        is_valid = False
        if validity_text:
            try:
                if "至" in validity_text:
                    parts = validity_text.split("至")
                    if len(parts) >= 2:
                        end_date_str = parts[1].strip()
                        
                        # 清理日期字符串
                        end_date_str = end_date_str.split(' ')[0]
                        end_date_str = end_date_str.split('\n')[0]
                        
                        # 处理中文日期格式
                        if "年" in end_date_str and "月" in end_date_str and "日" in end_date_str:
                            end_date_str = end_date_str.replace("年", "-").replace("月", "-").replace("日", "")
                        elif "年" in end_date_str:
                            end_date_str = end_date_str.replace("年", "-")
                        
                        # 清理非数字和连字符的字符
                        end_date_str = ''.join(c for c in end_date_str if c.isdigit() or c == '-')
                        
                        # 确保日期格式正确
                        if len(end_date_str) >= 8 and end_date_str.count('-') >= 2:
                            try:
                                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                            except:
                                try:
                                    end_date = datetime.strptime(end_date_str, "%Y-%m")
                                    end_date = end_date.replace(day=1)
                                except:
                                    end_date = None
                            
                            if end_date:
                                cutoff_date = datetime(2025, 12, 31)
                                is_valid = end_date >= cutoff_date
                                print(f"  有效期至: {end_date_str}, 是否有效: {is_valid}")
                            else:
                                is_valid = False
                        else:
                            is_valid = False
                    else:
                        is_valid = False
                
            except Exception as date_error:
                print(f"  日期解析错误: {date_error}")
                is_valid = False
        else:
            print("  未找到有效期信息")
            is_valid = False
        
        # 返回列表页
        print("  返回列表页...")
        await page.go_back()
        await human_wait(1, 2)
        
        # 确保返回到正确的页面
        try:
            await page.wait_for_selector(".list_ul", timeout=5000)
        except:
            print("  返回列表页后等待超时，但继续执行")
        
        return is_valid
        
    except Exception as e:
        print(f"  审核数据项时出错: {e}")
        try:
            await page.go_back()
            await human_wait(1, 2)
        except:
            pass
        return False

async def can_go_to_next_page(page):
    """检查是否可以翻到下一页"""
    try:
        # 查找下一页按钮
        next_page_button = page.locator("a.ant-pagination-item-link").locator("i.anticon-right")
        if await next_page_button.count() > 0:
            # 检查下一页按钮是否可点击（没有被禁用）
            parent_item = next_page_button.locator("xpath=../..")  # 获取父级元素
            if await parent_item.count() > 0:
                class_attribute = await parent_item.get_attribute("class")
                if class_attribute and "ant-pagination-disabled" not in class_attribute:
                    return True
        return False
    except Exception as e:
        print(f"检查下一页按钮时出错: {e}")
        return False

async def go_to_next_page(page):
    """翻到下一页 - 关键操作3：点击翻页之后检查滑块"""
    try:
        print("正在翻到下一页...")
        next_page_button = page.locator("a.ant-pagination-item-link").locator("i.anticon-right")
        await next_page_button.click()
        await human_wait(3, 5)  # 增加翻页等待时间
        
        # 检查翻页后的滑块
        await check_and_handle_slider(page)
        
        # 等待新页面加载
        await page.wait_for_selector(".list_ul", timeout=15000)
        await human_wait(1, 2)
        print("成功翻到下一页")
        return True
    except Exception as e:
        print(f"翻页失败: {e}")
        return False

async def scrape_page(page, province):
    """抓取所有页面的数据（支持翻页）"""
    all_valid_data = []
    current_page = 1
    
    print(f"开始抓取 {province} 的数据...")
    
    while True:
        print(f"正在处理第 {current_page} 页...")
        
        try:
            # 等待列表加载
            await page.wait_for_selector(".list_ul", timeout=15000)
            await human_wait(0.5, 1)
            
            # 获取所有列表项
            list_items = page.locator(".list_li")
            count = await list_items.count()
            print(f"本页找到 {count} 条记录")
            
            if count == 0:
                print("本页没有数据")
            else:
                # 处理当前页的所有数据项
                for i in range(count):
                    try:
                        # 重新获取列表项
                        list_items = page.locator(".list_li")
                        item = list_items.nth(i)
                        
                        # 提取机构名称
                        title_element = item.locator(".title_text")
                        name = await title_element.inner_text()
                        name = name.replace('\n', '').strip()
                        
                        # 提取成立时间
                        established_text = ""
                        text_spans = item.locator(".text_span")
                        text_count = await text_spans.count()
                        
                        for j in range(min(text_count, 5)):
                            span_text = await text_spans.nth(j).inner_text()
                            if "成立时间:" in span_text:
                                established_text = span_text.replace("成立时间:", "").strip()
                                break
                        
                        print(f"  审核第 {i+1} 项: {name}")
                        print(f"  成立时间: {established_text}")
                        
                        # 审核数据项有效性
                        is_valid = await check_item_validity(page, i)
                        
                        if is_valid:
                            all_valid_data.append({
                                "name": name,
                                "province": province,
                                "date": established_text
                            })
                            print(f"  通过审核 - 累计有效: {len(all_valid_data)}")
                        else:
                            print(f"  未通过审核")
                        
                        await human_wait(0.3, 0.8)
                        
                    except Exception as e:
                        print(f"  处理第 {i+1} 条数据时出错: {e}")
                        continue
            
            print(f"第 {current_page} 页完成，找到 {len(all_valid_data)} 条有效数据")
            
            # 检查是否可以翻到下一页
            if await can_go_to_next_page(page):
                # 翻到下一页
                if await go_to_next_page(page):
                    current_page += 1
                    continue
                else:
                    print("翻页失败，停止抓取")
                    break
            else:
                print("没有下一页，抓取完成")
                break
                
        except Exception as e:
            print(f"处理第 {current_page} 页时出错: {e}")
            break
    
    print(f"{province} 抓取完成，总共找到 {len(all_valid_data)} 条有效数据")
    return all_valid_data