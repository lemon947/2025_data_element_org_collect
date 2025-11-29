# all_main.py
#循环31个省份采集数据
import os
import json
from kimi_agent import create_kimi_agent  # 引入你写好的智能体
from dotenv import load_dotenv

load_dotenv()

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
os.makedirs(output_dir, exist_ok=True)


def query_province_with_agent(agent, province: str):
    """
    使用 LLMChain 智能体查询省份 JSON。
    """
    try:
        result_text = agent.invoke({"province": province})["text"]
    except Exception as e:
        print(f"调用智能体失败：{e}")
        return []

    # 尝试解析 JSON
    try:
        return json.loads(result_text)
    except Exception:
        print(f"⚠ 警告：模型返回的内容无法解析为 JSON：\n{result_text}")
        return result_text


# 3. 主程序入口
if __name__ == "__main__":
    print("正在初始化 Kimi 智能体...")
    agent = create_kimi_agent()

    print("\n===== 开始批量查询 31 个省份的数据局信息 =====\n")

    for province_name in provinces:
        print(f"查询中：{province_name} ...")

        result = query_province_with_agent(agent, province_name)

        # 保存到文件
        out_path = os.path.join(output_dir, f"{province_name}_data_bureaus.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✔ {province_name} 结果已保存：{out_path}\n")

    print("🎉 所有省份数据获取完成！")

