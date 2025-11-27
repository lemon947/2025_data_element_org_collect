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
    
    # 创建自定义指令
    custom_instruction = """
你是一个社会组织数据抓取助手。用户会输入省份名称，你需要调用相应的工具来抓取数据。

使用规则：
- 当用户输入单个省份时，使用social_organization_scraper工具
- 当用户输入"所有省份"、"全国"或要求抓取全部数据时，使用batch_social_organization_scraper工具，参数是31个省份！
- 当用户输入多个具体省份时，使用batch_social_organization_scraper工具
- 当用户询问可抓取的省份时，使用get_available_provinces工具

所有31个省份列表：北京市,天津市,河北省,山西省,内蒙古自治区,辽宁省,吉林省,黑龙江省,上海市,江苏省,浙江省,安徽省,福建省,江西省,山东省,河南省,湖北省,湖南省,广东省,广西壮族自治区,海南省,重庆市,四川省,贵州省,云南省,西藏自治区,陕西省,甘肃省,青海省,宁夏回族自治区,新疆维吾尔自治区

"""
    
    # 合并自定义指令和标准模板
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
    all_province_keywords = ["所有省份", "全部省份", "全国", "31个省份", "所有"]
    if user_input in all_province_keywords:
        return True, VALID_PROVINCES
    
    # 处理中文逗号，统一转换为英文逗号
    normalized_input = user_input.replace('，', ',')
    
    # 分割输入并清理空格
    provinces = [p.strip() for p in normalized_input.split(',')]
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
    """处理用户输入并调用Agent"""
    try:
        print(f"用户输入: '{user_input}'")
        
        # 验证输入格式 - 这里已经验证了省份有效性
        is_valid, provinces = validate_province_input(user_input)
        
        if not is_valid:
            return "输入格式错误！请确保省份名称与列表完全一致，多个省份用逗号分隔，或输入'所有省份'抓取全国数据。"
        
        if not provinces:
            return "未识别到有效的省份名称，请重新输入"
        
        print(f"识别到 {len(provinces)} 个有效省份")
        
        # 直接让Agent处理，Agent会根据prompt规则选择工具
        response = agent_executor.invoke({
            "input": user_input
        })
        
        return response['output']
        
    except Exception as e:
        error_msg = f"处理请求时出错: {str(e)}"
        print(error_msg)
        return error_msg

def main():
    """主函数"""
    print("=== 社会组织数据抓取Agent ===")
    print("\n欢迎使用！本系统可以帮您抓取各省份的社会组织数据。")
    
    display_provinces()
    
    print("\n输入格式说明:")
    print("1. 单个省份: 直接输入省份名称，如: 北京市")
    print("2. 多个省份: 用逗号分隔，如: 北京市,上海市,广东省")
    print("3. 所有省份: 输入'所有省份'或'全国'抓取31个省份的全部数据")
    print("4. 退出程序: 输入'退出'")
    print("\n注意: 请严格按照上方列表中的省份名称输入！")
    
    print("\n初始化Agent中...")
    agent_executor = initialize_agent()
    print("Agent初始化完成")
    
    while True:
        try:
            user_input = input("\n请输入省份名称: ").strip()
            
            exit_keywords = ['退出', 'exit', 'quit']
            if user_input.lower() in exit_keywords:
                print("感谢使用，再见！")
                break
            
            if not user_input:
                print("请输入有效的省份名称")
                continue
            
            response = process_user_input(user_input, agent_executor)
            print(f"\n执行结果:\n{response}") #在agent执行后打印结果
            
        except KeyboardInterrupt:
            print("\n\n用户中断程序，再见！")
            break
        except Exception as e:
            print(f"系统执行出错: {e}")

if __name__ == "__main__":
    main()