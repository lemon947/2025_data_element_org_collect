from openai import OpenAI
import os
import json
from dotenv import load_dotenv  
load_dotenv()

def query_province_data_bureau(province: str):
    """
    调用 Kimi 模型获取指定省份的数据局信息
    """
    client = OpenAI(
        api_key=os.getenv("MOONSHOT_API_KEY"),  # 或直接写你的 Key
        base_url="https://api.moonshot.cn/v1"
    )

    system_message = """
    你的任务是：用户会提供中国某省份名称，你需要查找各个可信数据源返回该省份下的省级数据局（数据管理部门、数据中心）的信息。（不要只给出1个）
    注意必须要给出准确无误可以打开的url链接作为依据来源！
    返回 JSON 格式如下：
    [
      {
        "集团名称": "xxx",
        "成立时间": "yyyy-mm-dd",
        “来源标题”："xxxx",
        "依据URL": "http://..."
      },
      {
        "集团名称": "xxx",
        "成立时间": "yyyy-mm-dd",
        “来源标题”："xxxx",
        "依据URL": "http://..."
      },
    ]
    要求：
    - 必须严格按照 JSON 输出，不要额外文字！
    - 如果没有相关部门，可以返回空列表 []
    - 只提供部门名称、成立时间和依据URL
    """

    user_message = f"{province}下的【所有】省级数据局（数据管理部门、数据中心）有哪些？请尽量查全信息到最后的json，不要有任何遗漏！"
    
    completion = client.chat.completions.create(  
        model="kimi-k2-turbo-preview",
        messages=[ 
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0.6,
    )

    result_text = completion.choices[0].message.content # 获取返回内容
    #从返回的 completion 结构中提取第一个候选的文本内容（即模型回复字符串）。
    
    try:
        result_json = json.loads(result_text) # 尝试将返回内容解析为 JSON
    except Exception:
        print("注意：返回内容无法解析为 JSON，原始内容如下：")
        result_json = result_text

    return result_json


if __name__ == "__main__":
    province_name = input("请输入省份名称: ").strip()
    result = query_province_data_bureau(province_name)
    #将json结果保存到文件
    #以 UTF-8 编码写入文件，使用 json.dump 将结果（JSON 或文本）保存为格式化的 JSON，ensure_ascii=False 保持中文字符不被转义。
    
    out_path = rf"C:\Users\PC\Desktop\研究生\研1\数据要素市场化推进力指数\2025数据\数据局结果\{province_name}_data_bureaus.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2) 
    print("结果 JSON:\n", json.dumps(result, ensure_ascii=False, indent=2))
