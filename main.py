# main.py
import os
import json
from dotenv import load_dotenv
from kimi_agent import create_kimi_agent

load_dotenv()

def query_province_data_bureau(province: str):
    """
    调用 Kimi 智能体，查询某省的数据局信息
    """
    agent = create_kimi_agent()
    result_text = agent.invoke({"province": province})["text"]

    # JSON 解析
    try:
        result_json = json.loads(result_text)
    except Exception:
        print("⚠️ 模型返回的内容无法解析为 JSON，原始内容如下：")
        print(result_text)
        return result_text

    return result_json


if __name__ == "__main__":
    province_name = input("请输入省份名称: ").strip()
    print(f"正在查询 {province_name} ...")

    result = query_province_data_bureau(province_name)

    output_dir = r"C:\Users\PC\Desktop\研究生\研1\数据要素市场化推进力指数\2025数据\数据局结果"
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, f"{province_name}_data_bureaus.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已保存至：{out_path}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
