# tools.py
from langchain.tools import tool
import asyncio
from playwright.async_api import async_playwright
from scraper import setup_browser, set_filters, scrape_page
import csv
import re

def clean_province_param(province_param: str) -> str:
    """清理省份参数，移除Agent传递的多余字符
    
    由于省份已经在agent_main.py中验证过，这里只做基本清理
    """
    print(f"原始参数: {repr(province_param)}")
    
    # 移除Observation文本（Agent添加的）
    if 'Observation' in province_param:
        province_param = province_param.split('Observation')[0].strip()
    
    # 移除所有引号，保留逗号分隔符
    cleaned = province_param.replace('"', '').replace("'", "")
    
    # 使用正则表达式保留中文字符和逗号
    cleaned = re.sub(r'[^\u4e00-\u9fff,]', '', cleaned)
    
    print(f"清理后参数: {repr(cleaned)}")
    return cleaned

@tool
def social_organization_scraper(province: str) -> str:
    """抓取单个省份的社会组织数据
    
    省份有效性已在agent_main.py中验证，这里直接使用
    """
    try:
        print(f"social_organization_scraper工具被调用")
        
        # 清理参数，移除Agent添加的多余字符
        province_clean = clean_province_param(province)
        
        # 基本参数检查
        if not province_clean:
            return "错误：省份参数为空"
        
        print(f"✅ 开始抓取: '{province_clean}'")
        
        # 执行实际的抓取逻辑
        result = asyncio.run(execute_scraper(province_clean))
        return result
        
    except Exception as e:
        error_msg = f"抓取 {province} 数据时出错: {str(e)}"
        print(error_msg)
        return error_msg

@tool  
def batch_social_organization_scraper(provinces: str) -> str:
    """批量抓取多个省份的社会组织数据
    
    省份有效性已在agent_main.py中验证，这里直接使用
    """
    try:
        print(f"batch_social_organization_scraper工具被调用")
        print(f"接收到的参数: {repr(provinces)}")
        
        # 清理参数，保留逗号分隔符
        provinces_clean = clean_province_param(provinces)
        if not provinces_clean:
            return "错误：省份参数为空"
        
        print(f"清理后的参数字符串: {repr(provinces_clean)}")
        
        # 分割省份 - 省份已经在agent_main.py中验证过，直接使用
        province_list = [p.strip() for p in provinces_clean.split(',')]
        province_list = [p for p in province_list if p]  # 只移除空字符串
        
        print(f"需要处理的省份数量: {len(province_list)}")
        print(f"省份列表: {province_list}")
        
        # 基本检查
        if not province_list:
            return "错误：没有有效的省份名称"
        
        results = []
        total_success = 0
        total_failed = 0
        
        # 循环处理每个省份
        for i, province in enumerate(province_list, 1):
            print(f"\n正在处理第 {i}/{len(province_list)} 个省份: {province}")
            
            try:
                # 执行单个省份的抓取
                result_text = asyncio.run(execute_scraper(province))
                
                # 根据结果文本判断成功与否
                if "成功" in result_text or "条记录" in result_text:
                    total_success += 1
                else:
                    total_failed += 1
                    
            except Exception as e:
                # 单个省份抓取失败不影响其他省份
                result_text = f"抓取 {province} 时发生异常: {str(e)}"
                total_failed += 1
            
            # 记录结果
            results.append(f"## {province} ##\n{result_text}")
            print(f"已完成: {i}/{len(province_list)}")
        
        # 生成汇总报告
        summary = f"\n批量抓取完成报告\n"
        summary += f"成功: {total_success} 个省份\n"
        summary += f"失败: {total_failed} 个省份\n"
        summary += f"总计处理: {len(province_list)} 个省份\n\n"
        
        return summary + "\n".join(results)
        
    except Exception as e:
        error_msg = f"批量抓取数据时出错: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def get_available_provinces() -> str:
    """获取所有可抓取的省份列表"""
    # 从agent_main.py导入省份列表
    from main import VALID_PROVINCES   #导入之前定义的省份
    province_list = "支持抓取的31个省份:\n" + "\n".join([
        f"{i+1}. {province}" for i, province in enumerate(VALID_PROVINCES)
    ])
    return province_list

async def execute_scraper(province: str) -> str:
    """执行具体的数据抓取逻辑"""
    try:
        #print(f"开始执行数据抓取 - 省份: '{province}'")
        
        # 启动浏览器
        async with async_playwright() as p:
            browser, page = await setup_browser(p)
            
            try:
                keyword = "数据"
                print(f"设置筛选条件 - 省份: '{province}', 关键词: '{keyword}'")
                
                # 设置筛选条件
                await set_filters(page, province, keyword)
                
                # 执行数据抓取
                print("开始抓取页面数据...")
                all_valid_data = await scrape_page(page, province)
                
                # 处理抓取结果
                if all_valid_data:
                    filename = rf"C:\Users\PC\Desktop\研究生\研1\数据要素市场化推进力指数\2025数据\行业协会\{province}_valid_social_orgs.csv"
                    
                    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.DictWriter(f, fieldnames=["name", "province", "date"])
                        writer.writeheader()
                        writer.writerows(all_valid_data)
                    
                    result = f"成功抓取 {province} 的社会组织数据，共 {len(all_valid_data)} 条记录。\n"
                    result += f"数据已保存到: {filename}"
                    return result
                else:
                    return f"在 {province} 没有找到符合条件的有效数据"
                    
            except Exception as e:
                return f"抓取 {province} 数据时出错: {str(e)}"
            finally:
                await browser.close()
                
    except Exception as e:
        return f"浏览器初始化失败: {str(e)}"