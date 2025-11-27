# agent_main.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.prompts import PromptTemplate
from tools import social_organization_scraper, batch_social_organization_scraper, get_available_provinces

# 加载环境变量
load_dotenv()

# 定义有效的省份列表
VALID_PROVINCES = [
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区",
    "辽宁省", "吉林省", "黑龙江省", "上海市", "江苏省",
    "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区",
    "海南省", "重庆市", "四川省", "贵州省", "云南省",
    "西藏自治区", "陕西省", "甘肃省", "青海省", "宁夏回族自治区",
    "新疆维吾尔自治区"
]

def initialize_agent():
    """初始化Agent和工具"""
    llm = ChatOpenAI(
        model="glm-4-plus",
        openai_api_key=os.getenv("ZHIPUAI_API_KEY"),
        openai_api_base="https://open.bigmodel.cn/api/paas/v4/",
        temperature=0.1,
    )
    
    tools = [
        social_organization_scraper,
        batch_social_organization_scraper,
        get_available_provinces,
    ]
    
    # 获取标准React prompt模板
    base_prompt = hub.pull("hwchase17/react")
    
    # 在标准模板前添加我们的自定义指令
    custom_instruction = """
你是一个社会组织数据抓取助手。用户会输入省份名称，你需要调用相应的工具来抓取数据。

使用规则：
- 当用户输入单个省份时，使用social_organization_scraper工具
- 当用户输入"所有省份"、"全国"或要求抓取全部数据时，使用batch_social_organization_scraper工具
- 当用户输入多个具体省份时，使用batch_social_organization_scraper工具
- 当用户询问可抓取的省份时，使用get_available_provinces工具

所有31个省份列表：北京市,天津市,河北省,山西省,内蒙古自治区,辽宁省,吉林省,黑龙江省,上海市,江苏省,浙江省,安徽省,福建省,江西省,山东省,河南省,湖北省,湖南省,广东省,广西壮族自治区,海南省,重庆市,四川省,贵州省,云南省,西藏自治区,陕西省,甘肃省,青海省,宁夏回族自治区,新疆维吾尔自治区

"""
    
    # 创建新的prompt模板，将自定义指令添加到标准模板前面
    custom_prompt_template = custom_instruction + base_prompt.template
    
    # 创建新的PromptTemplate
    custom_prompt = PromptTemplate(
        template=custom_prompt_template,
        input_variables=base_prompt.input_variables,
        partial_variables=base_prompt.partial_variables
    )
    
    agent = create_react_agent(llm, tools, custom_prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )
    
    return agent_executor

def display_provinces():
    """显示所有可用的省份列表"""
    print("\n" + "="*60)
    print("                   可抓取的31个省份列表")
    print("="*60)
    
    for i in range(0, len(VALID_PROVINCES), 3):
        row = []
        for j in range(3):
            if i + j < len(VALID_PROVINCES):
                index = i + j + 1
                province = VALID_PROVINCES[i + j]
                row.append(f"{index:2d}. {province}")
        print("  ".join(row))
    
    print("="*60)

def validate_province_input(user_input: str) -> tuple[bool, list]:
    """验证用户输入的省份格式"""
    if not user_input.strip():
        return False, []
    
    # 检查是否是"所有省份"的关键词
    if user_input in ["所有省份", "全部省份", "全国", "31个省份", "所有"]:
        return True, VALID_PROVINCES
    
    # 分割输入
    provinces = [p.strip() for p in user_input.replace('，', ',').split(',')]
    provinces = [p for p in provinces if p]
    
    # 检查每个省份是否在有效列表中
    invalid_provinces = []
    valid_provinces = []
    
    for province in provinces:
        if province in VALID_PROVINCES:
            valid_provinces.append(province)
        else:
            invalid_provinces.append(province)
    
    return len(invalid_provinces) == 0, valid_provinces

def process_user_input(user_input: str, agent_executor: AgentExecutor) -> str:
    """处理用户输入，让Agent决定使用哪个工具"""
    try:
        print(f"DEBUG: 用户输入: '{user_input}'")
        
        # 验证输入格式
        is_valid, provinces = validate_province_input(user_input)
        
        if not is_valid:
            return "输入格式错误！请确保省份名称与列表完全一致，多个省份用逗号分隔，或输入'所有省份'抓取全国数据。"
        
        if not provinces:
            return "未识别到有效的省份名称，请重新输入"
        
        # 直接让Agent处理，不指定具体工具
        response = agent_executor.invoke({
            "input": user_input
        })
        
        return response['output']
    except Exception as e:
        return f"处理请求时出错: {e}"

def main():
    """主函数"""
    print("=== 社会组织数据抓取Agent ===")
    print("\n欢迎使用！本系统可以帮您抓取各省份的社会组织数据。")
    
    # 显示省份列表
    display_provinces()
    
    print("\n输入格式说明:")
    print("1. 单个省份: 直接输入省份名称，如: 北京市")
    print("2. 多个省份: 用逗号分隔，如: 北京市,上海市,广东省")
    print("3. 所有省份: 输入'所有省份'或'全国'抓取31个省份的全部数据")
    print("4. 输入'退出'结束程序")
    print("\n注意: 请严格按照上方列表中的省份名称输入！")
    
    # 初始化Agent
    agent_executor = initialize_agent()
    
    while True:
        user_input = input("\n请输入省份名称: ").strip()
        
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("感谢使用，再见！")
            break
        
        if not user_input:
            print("请输入有效的省份名称")
            continue
        
        try:
            # 让Agent处理请求
            response = process_user_input(user_input, agent_executor)
            print(f"\n{response}")
        except Exception as e:
            print(f"系统执行出错: {e}")

if __name__ == "__main__":
    main()