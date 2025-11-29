# kimi_agent.py
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

load_dotenv()

def create_kimi_agent():
    """
    创建一个基于 Kimi 模型、无工具的最简智能体
    """

    # 1. 初始化 LLM（Kimi）
    llm = ChatOpenAI(
        model="kimi-k2-turbo-preview",
        openai_api_key=os.getenv("MOONSHOT_API_KEY"),
        openai_api_base="https://api.moonshot.cn/v1",
        temperature=0.2
    )

    # 2. Prompt：严格 JSON，仅输出真实信息
    prompt = PromptTemplate(
        input_variables=["province"],
        template="""
你是一个精确的数据查询智能体。用户将提供一个中国省级行政区名称。
你需要根据公开可查的真实信息，返回该省份下面【所有】省级数据局、数据管理部门或大数据中心的信息。

务必遵守：
- 只能输出 JSON 数组，不要任何额外解释或文字
- 每个对象必须包含：集团名称、成立时间、来源标题、依据URL
- URL 必须真实存在且可打开
- 你需要尽量“查全”，不能漏掉能查到的部门

JSON 输出格式示例：
[
  {
    "集团名称": "xxx",
    "成立时间": "yyyy-mm-dd",
    "来源标题": "xxxx",
    "依据URL": "http://example.com"
  }
]

请输出 {province} 的全部省级数据管理部门（严格 JSON）。
"""
    )

    # 3. 构建 LLMChain 作为简单 Agent
    agent = LLMChain(
        llm=llm,
        prompt=prompt
    )

    return agent
