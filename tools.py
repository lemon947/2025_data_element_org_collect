# tools.py
from langchain.tools import tool
import asyncio
from playwright.async_api import async_playwright
from scraper import setup_browser, set_filters, scrape_page
import csv
import re

VALID_PROVINCES = [
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
    "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
    "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
    "海南省", "重庆市", "四川省", "贵州省", "云南省",
    "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
    "新疆维吾尔自治区"
]

def clean_province_param(province: str) -> str:
    """清理省份参数，移除多余的引号和Observation文本，但保留逗号"""
    print(f"🔧 原始参数: {repr(province)}")
    
    # 首先移除Observation文本
    if 'Observation' in province:
        province = province.split('Observation')[0].strip()
    
    # 移除所有引号，但保留逗号
    cleaned = province.replace('"', '').replace("'", "")
    
    # 移除其他可能的特殊字符，但保留逗号和中文字符
    cleaned = re.sub(r'[^\u4e00-\u9fff,]', '', cleaned)
    
    print(f"🔧 清理后参数: {repr(cleaned)}")
    return cleaned

@tool
def social_organization_scraper(province: str) -> str:
    """抓取单个省份的社会组织数据。当用户输入单个省份名称如'北京市'时使用此工具。
    
    Args:
        province: 省份名称，如'北京市'
        
    Returns:
        str: 抓取结果信息
    """
    try:
        print(f"🔧 social_organization_scraper工具被调用")
        
        # 清理参数
        province_clean = clean_province_param(province)
        
        if not province_clean:
            return "错误：省份参数为空"
        
        # 验证参数
        if province_clean not in VALID_PROVINCES:
            return f"错误：'{province_clean}' 不是有效的省份名称。有效省份包括：北京市、天津市、河北省等。"
        
        print(f"✅ 参数验证通过，开始抓取: '{province_clean}'")
        result = asyncio.run(execute_scraper(province_clean))
        return result
    except Exception as e:
        return f"抓取数据时出错: {str(e)}"

@tool  
def batch_social_organization_scraper(provinces: str) -> str:
    """批量抓取多个省份的社会组织数据。当用户输入多个省份或要求抓取所有省份时使用此工具。
    
    此工具会逐个处理每个省份，抓取社会组织数据并保存到CSV文件。
    
    Args:
        provinces: 逗号分隔的省份名称字符串，如'北京市,上海市,广东省'
        
    Returns:
        str: 所有省份的抓取结果汇总
    """
    try:
        print(f"🔧 batch_social_organization_scraper工具被调用")
        print(f"🔧 接收到的参数: {repr(provinces)}")
        
        # 清理参数 - 保留逗号
        provinces_clean = clean_province_param(provinces)
        if not provinces_clean:
            return "错误：省份参数为空"
        
        print(f"🔧 清理后的参数字符串: {repr(provinces_clean)}")
        
        # 分割省份 - 使用逗号分割
        province_list = [p.strip() for p in provinces_clean.split(',')]
        province_list = [p for p in province_list if p and p in VALID_PROVINCES]  # 只保留有效省份
        
        print(f"🔧 有效省份数量: {len(province_list)}")
        print(f"🔧 有效省份列表: {province_list}")
        
        # 如果没有有效省份，直接返回
        if not province_list:
            return "错误：没有找到有效的省份名称"
        
        results = []
        total_success = 0
        total_failed = 0
        
        # 循环处理每个省份
        for i, province in enumerate(province_list, 1):
            print(f"\n📋 正在处理第 {i}/{len(province_list)} 个省份: {province}")
            
            try:
                result_text = asyncio.run(execute_scraper(province))
                if "成功" in result_text or "条记录" in result_text:
                    total_success += 1
                else:
                    total_failed += 1
            except Exception as e:
                result_text = f"❌ 抓取 {province} 时发生异常: {str(e)}"
                total_failed += 1
            
            results.append(f"## {province} ##\n{result_text}")
            
            # 添加进度信息
            print(f"✅ 已完成: {i}/{len(province_list)}")
        
        # 汇总结果
        summary = f"\n📊 批量抓取完成！\n"
        summary += f"✅ 成功: {total_success} 个省份\n"
        summary += f"❌ 失败: {total_failed} 个省份\n"
        summary += f"📁 总计: {len(province_list)} 个省份\n\n"
        
        return summary + "\n".join(results)
    except Exception as e:
        return f"批量抓取数据时出错: {str(e)}"

@tool
def get_available_provinces() -> str:
    """获取所有可抓取的省份列表。"""
    return "支持抓取的31个省份:\n" + "\n".join([f"{i+1}. {province}" for i, province in enumerate(VALID_PROVINCES)])

async def execute_scraper(province: str) -> str:
    """执行具体的数据抓取逻辑"""
    try:
        print(f"🎯 开始执行数据抓取 - 省份: '{province}'")
        
        async with async_playwright() as p:
            browser, page = await setup_browser(p)
            
            try:
                keyword = "数据"
                print(f"🎯 设置筛选条件 - 省份: '{province}', 关键词: '{keyword}'")
                
                await set_filters(page, province, keyword)
                
                print("🎯 开始抓取页面数据...")
                all_valid_data = await scrape_page(page, province)
                
                if all_valid_data:
                    filename = rf"C:\Users\PC\Desktop\研究生\研1\数据要素市场化推进力指数\{province}_valid_social_orgs.csv"
                    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.DictWriter(f, fieldnames=["name", "province", "date"])
                        writer.writeheader()
                        writer.writerows(all_valid_data)
                    
                    result = f"✅ 成功抓取 {province} 的社会组织数据，共 {len(all_valid_data)} 条记录。\n"
                    result += f"📁 数据已保存到: {filename}"
                    return result
                else:
                    return f"❌ 在 {province} 没有找到符合条件的有效数据"
                    
            except Exception as e:
                return f"❌ 抓取 {province} 数据时出错: {str(e)}"
            finally:
                await browser.close()
                
    except Exception as e:
        return f"❌ 浏览器初始化失败: {str(e)}"