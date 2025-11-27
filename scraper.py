import asyncio
import random

# 模拟人类等待
async def human_wait(a=0.5, b=1.5):
    await asyncio.sleep(random.uniform(a, b))

# 设置浏览器
async def setup_browser(p):
    browser = await p.chromium.launch(
        headless=False, 
        slow_mo=100,
        timeout=60000
    )
    
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ignore_https_errors=True
    )
    
    page = await context.new_page()
    
    print("正在打开目标网站...")
    await page.goto("https://xxgs.chinanpo.mca.gov.cn/gsxt/newList", 
                  wait_until="domcontentloaded",
                  timeout=60000)
    print("页面加载成功")
    await human_wait(2, 3)
    
    return browser, page

# 设置筛选条件
async def set_filters(page, province, keyword):
    print("设置筛选条件...")
    
    # 点击组织状态：正常
    print("点击组织状态：正常")
    normal_status = page.locator("text=正常").first
    await normal_status.click()
    await human_wait(1, 2)

    # 点击信用状况：正常
    print("点击信用状况：正常")
    normal_credit = page.locator("text=正常").nth(1)
    await normal_credit.click()
    await human_wait(1, 2)

    # 点击组织类型：社会团体
    print("点击组织类型：社会团体")
    social_group = page.locator("text=社会团体").first
    await social_group.click()
    await human_wait(1, 2)

    # 输入关键词
    print(f"正在输入搜索关键词: {keyword}")
    search_input = page.locator("input[placeholder='请输入社会组织名称或统一社会信用代码']")
    await search_input.fill(keyword)
    await human_wait(1, 2)

    # 点击旁边空白区域关闭可能的下拉菜单
    print("点击空白区域关闭下拉菜单...")
    await page.mouse.click(200, 150)
    await human_wait(1, 2)

    # 选择省份
    print(f"正在选择省份: {province}")
    province_dropdown = page.locator(".ant-select-selection").first
    await province_dropdown.click()
    await human_wait(1, 2)
    
    province_option = page.locator(f"text={province}").first
    await province_option.click()
    await human_wait(1, 2)

    # 点击搜索
    print("正在执行搜索...")
    search_button = page.locator(".search_button").first
    await search_button.click()
    await human_wait(3, 4)

    # 检查滑块验证
    if await page.locator("text=请完成安全验证").count() > 0:
        print("检测到滑块验证，请人工完成滑块...")
        input("完成后按回车继续...")
        await human_wait(2, 3)

# 检查数据项是否有效（在2025-12-31之前有效）
async def check_item_validity(page, item_index):
    try:
        # 保存当前页面URL，用于异常时恢复
        current_url = page.url
        
        # 重新获取列表项，防止Stale元素引用
        list_items = page.locator(".list_li")
        item = list_items.nth(item_index)
        
        # 点击标题进入详情页（不是点击整个列表项）
        title_element = item.locator(".title_text")
        print(f"  点击标题进入详情页...")
        await title_element.click()
        await human_wait(3, 4)  # 增加等待时间
        
        # 等待详情页加载 - 使用多种策略
        try:
            # 策略1: 等待页面导航完成
            await page.wait_for_load_state('networkidle')
            await human_wait(1, 2)
            
            # 策略2: 检查是否成功跳转到详情页
            current_url = page.url
            if "detail" in current_url or "newList" not in current_url:
                print(f"  成功跳转到详情页: {current_url}")
            else:
                print(f"  可能仍在列表页，URL: {current_url}")
            
            # 策略3: 尝试多种选择器查找有效期信息
            selectors_to_try = [
                ".data_span.text",
                ".data_span",
                ".text_span",
                ".ant-descriptions-item-content",
                ".ant-card-body",
                "span[class*='data']",
                "span[class*='text']",
                ".ant-timeline-item-content",
                "div[class*='content']"
            ]
            
            validity_text = ""
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    elements = page.locator(selector)
                    count = await elements.count()
                    for i in range(min(count, 15)):  # 检查前15个元素
                        element_text = await elements.nth(i).inner_text()
                        element_text_clean = element_text.replace('\n', ' ').strip()
                        if "至" in element_text_clean and ("年" in element_text_clean or "-" in element_text_clean):
                            validity_text = element_text_clean
                            print(f"  使用选择器 '{selector}' 找到有效期信息: {validity_text}")
                            break
                    if validity_text:
                        break
                except:
                    continue
            
            # 如果没找到，尝试更通用的文本搜索
            if not validity_text:
                print("  尝试通用文本搜索有效期信息...")
                page_text = await page.inner_text("body")
                lines = page_text.split('\n')
                for line in lines:
                    line_clean = line.strip()
                    if "至" in line_clean and ("年" in line_clean or "-" in line_clean):
                        validity_text = line_clean
                        print(f"  从页面文本找到有效期: {validity_text}")
                        break
        
        except Exception as load_error:
            print(f"  详情页加载异常: {load_error}")
            # 尝试直接获取页面文本
            try:
                page_text = await page.inner_text("body")
                if "有效期" in page_text or "至" in page_text:
                    lines = page_text.split('\n')
                    for line in lines:
                        line_clean = line.strip()
                        if "至" in line_clean and ("年" in line_clean or "-" in line_clean):
                            validity_text = line_clean
                            print(f"  从页面文本找到有效期: {validity_text}")
                            break
            except:
                pass
        
        # 检查是否在2025-12-31之前有效
        is_valid = False
        if validity_text:
            try:
                # 提取结束日期
                if "至" in validity_text:
                    # 分割字符串，取结束日期部分
                    parts = validity_text.split("至")
                    if len(parts) >= 2:
                        end_date_str = parts[1].strip()
                        
                        # 清理日期字符串
                        end_date_str = end_date_str.split(' ')[0]  # 去除可能的时间部分
                        end_date_str = end_date_str.split('\n')[0]  # 去除换行
                        end_date_str = end_date_str.split('（')[0]  # 去除括号内容
                        end_date_str = end_date_str.split('(')[0]   # 去除英文括号内容
                        
                        # 处理中文日期格式
                        if "年" in end_date_str and "月" in end_date_str and "日" in end_date_str:
                            end_date_str = end_date_str.replace("年", "-").replace("月", "-").replace("日", "")
                        elif "年" in end_date_str:
                            end_date_str = end_date_str.replace("年", "-")
                        
                        # 清理多余的字符
                        end_date_str = ''.join(c for c in end_date_str if c.isdigit() or c == '-')
                        
                        # 确保日期格式正确
                        if len(end_date_str) >= 8 and end_date_str.count('-') >= 2:
                            from datetime import datetime
                            # 尝试解析日期
                            try:
                                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                            except:
                                # 如果标准格式失败，尝试其他格式
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
                                print(f"  无法解析日期: {end_date_str}")
                                is_valid = False
                        else:
                            print(f"  日期格式异常: {end_date_str}")
                            is_valid = False
                    else:
                        print(f"  有效期格式异常: {validity_text}")
                        is_valid = False
                
            except Exception as date_error:
                print(f"  日期解析错误: {date_error}, 原始文本: {validity_text}")
                is_valid = False
        else:
            print("  未找到有效期信息")
            is_valid = False
        
        # 返回上一页
        print("  返回列表页...")
        await page.go_back()
        await human_wait(2, 3)
        
        # 确保返回到正确的页面
        try:
            await page.wait_for_selector(".list_ul", timeout=10000)
            print("  成功返回列表页")
        except:
            print("  返回列表页后等待超时，但继续执行")
        
        return is_valid
        
    except Exception as e:
        print(f"  审核数据项时出错: {e}")
        # 出错时尝试多种方式恢复
        try:
            # 尝试返回上一页
            await page.go_back()
            await human_wait(2, 3)
        except:
            try:
                # 如果返回失败，尝试重新加载列表页
                await page.goto("https://xxgs.chinanpo.mca.gov.cn/gsxt/newList")
                await human_wait(3, 4)
                # 重新设置筛选条件
                await set_filters(page)
            except:
                pass
        return False

# 抓取单页数据并审核（修改版本）
async def scrape_page(page, province):
    try:
        # 等待列表加载
        await page.wait_for_selector(".list_ul", timeout=15000)
        await human_wait(1, 2)
        
        # 获取所有列表项
        list_items = page.locator(".list_li")
        count = await list_items.count()
        print(f"本页找到 {count} 条记录")
        
        if count == 0:
            return []
            
        valid_data = []
        for i in range(count):
            try:
                # 在点击前重新获取列表项，防止Stale元素引用
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
                
                for j in range(text_count):
                    span_text = await text_spans.nth(j).inner_text()
                    if "成立时间:" in span_text:
                        established_text = span_text.replace("成立时间:", "").strip()
                        break
                
                print(f"\n  审核第 {i+1} 项: {name}")
                print(f"  成立时间: {established_text}")
                
                # 审核数据项有效性
                is_valid = await check_item_validity(page, i)
                
                if is_valid:
                    valid_data.append({
                        "name": name,
                        "province": province,
                        "date": established_text
                    })
                    print(f"  ✓ 通过审核 - 累计有效: {len(valid_data)}")
                else:
                    print(f"  ✗ 未通过审核")
                
                # 审核后等待一下
                await human_wait(1, 2)
                
            except Exception as e:
                print(f"处理第 {i+1} 条数据时出错: {e}")
                continue
                
        return valid_data
    except Exception as e:
        print(f"抓取页面数据时出错: {e}")
        return []