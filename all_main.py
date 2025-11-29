# all_main.py
from main import query_province_data_bureau  # 假设 main.py 在同一目录下
import os
import json

# 1. 中国 31 个省份列表（不含港澳台）
provinces = [
    "北京市", "天津市", 
    "河北省", "山西省", "内蒙古自治区",
    "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
    "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
    "海南省", "重庆市", "四川省", "贵州省", "云南省",
    "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
    "新疆维吾尔自治区"
]

# 2. 输出文件目录
output_dir = r"C:\Users\PC\Desktop\研究生\研1\数据要素市场化推进力指数\2025数据\数据局结果"
os.makedirs(output_dir, exist_ok=True)  # 如果目录不存在则创建

# 3. 循环每个省份
for province_name in provinces:
    print(f"正在查询 {province_name} 数据局信息...")
    try:
        result = query_province_data_bureau(province_name)
    except Exception as e:
        print(f"查询 {province_name} 时出错: {e}")
        result = []

    # 4. 保存到对应文件
    out_path = os.path.join(output_dir, f"{province_name}_data_bureaus.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"{province_name} 数据局信息已保存到 {out_path}\n")

print("所有省份数据局信息获取完成！")
