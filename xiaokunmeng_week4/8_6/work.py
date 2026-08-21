import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda

load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(model_name=model_name,api_key=api_key,base_url=base_url,temperature=0.7)
core_llm = ChatOpenAI(model_name=model_name,api_key=api_key,base_url=base_url,temperature=0.1)

def call_advisors(inputs):
    """根据顾问列表中选择最合适的顾问"""
    dept_list = [d.strip() for d in inputs.get("department", "").split(",") if d.strip()]
    tasks = {}
    if "destination" in dept_list:
        tasks["destination"] = destination_chain
    if "budget" in dept_list:
        tasks["budget"] = budget_chain
    if "transportation" in dept_list:
        tasks["transportation"] = transportation_chain
    if "food" in dept_list:
        tasks["food"] = food_chain
    if "culture" in dept_list:
        tasks["culture"] = culture_chain
    if not tasks:
        return "unknown"
    parallel_chain = RunnableParallel(tasks)
    results = parallel_chain.invoke(inputs)
    summary = []
    for advisor_name, result in results.items():
        summary.append(f"{advisor_name}: \n{result}")
    return "\n".join(summary)
core_prompt = ChatPromptTemplate.from_template(
    """
    你是一个旅行计划主管。请根据客户的问题：【{question}】，决定需要哪些旅行顾问来参与回答。
    你只能从以下五个选项中选择输出（可以同时选择多个，用英文逗号分隔）：
    1. destination   — 如果问题涉及目的地的选择、景点推荐、天气、最佳旅行季节等
    2. budget        — 如果问题涉及预算规划、费用估算、省钱技巧等
    3. transportation— 如果问题涉及交通方式（飞机、火车、租车等）、路线规划、交通成本等
    4. food          — 如果问题涉及美食推荐、当地特色餐厅、饮食文化等
    5. culture       — 如果问题涉及文化习俗、历史背景、节庆活动、礼仪规范等
    如果问题不涉及以上任何方面，请只输出 "unknown"。
    你的输出（如果用户特地强调就输出相关的输出选项列表，如 "destination, budget, transportation"，否则默认选择所有选项）：
    """
)
core_chain = core_prompt | core_llm | StrOutputParser()

destination_prompt = ChatPromptTemplate.from_template(
    """
    你是一位资深的目的地顾问，擅长根据用户需求推荐最佳旅行目的地。
    用户信息：
    - 目的地：{destination}
    - 旅行天数：{days} 天
    - 预算：{budget} 元
    请根据以上信息，提供以下建议：
    1. 推荐该目的地最适合的季节和天气情况
    2. 推荐 3-5 个必去的景点（包含门票参考价格）
    3. 推荐当地的特色体验活动
    4. 给出每日行程的初步建议（按天分配）
    输出格式：请使用清晰的分段结构，方便阅读。
    """
)
destination_chain = destination_prompt | llm | StrOutputParser()

budget_prompt = ChatPromptTemplate.from_template(
    """
    你是一位精明的预算规划师，擅长帮助旅行者在预算内最大化旅行体验。
    用户信息：
    - 目的地：{destination}
    - 旅行天数：{days} 天
    - 总预算：{budget} 元
    请根据以上信息，提供以下建议：
    1. 预算分配建议（住宿、餐饮、交通、门票、购物等类别）
    2. 每个类别的预估费用范围
    3. 省钱技巧（如提前预订、当地交通选择等）
    4. 如果预算紧张，提供替代方案
    输出格式：使用表格或分类列表清晰展示预算分配。
    """
)
budget_chain = budget_prompt | llm | StrOutputParser()

transportation_prompt = ChatPromptTemplate.from_template(
    """
    你是一位交通规划专家，擅长为旅行者设计最优的出行路线。
    用户信息：
    - 目的地：{destination}
    - 出发地：{origin}（如未提供则默认从用户所在地出发）
    - 旅行天数：{days} 天
    请根据以上信息，提供以下建议：
    1. 从出发地到目的地的最佳交通方式（飞机/火车/自驾等）及费用
    2. 目的地内部的交通建议（地铁、公交、打车、租车等）
    3. 交通总成本估算
    4. 通勤时间优化建议
    输出格式：分步骤说明，清晰易读。
    """
)
transportation_chain = transportation_prompt | llm | StrOutputParser()

food_prompt = ChatPromptTemplate.from_template(
    """
    你是一位美食达人，熟悉各地的特色美食和餐厅。
    用户信息：
    - 目的地：{destination}
    - 旅行天数：{days} 天
    - 预算：{budget} 元（已分配餐饮部分）
    请根据以上信息，提供以下建议：
    1. 当地必吃的 5-8 道特色菜
    2. 推荐 3-5 家当地口碑餐厅（含人均消费）
    3. 当地特色小吃街或夜市推荐
    4. 每日餐饮安排建议（早、中、晚餐推荐）
    输出格式：按餐厅或菜品分类，附上简短评价。
    """
)
food_chain = food_prompt | llm | StrOutputParser()

culture_prompt = ChatPromptTemplate.from_template(
    """
    你是一位文化学者，熟悉各地的历史、文化和习俗。
    用户信息：
    - 目的地：{destination}
    - 旅行天数：{days} 天
    请根据以上信息，提供以下建议：
    1. 目的地的历史背景简介
    2. 当地特色文化习俗和节日活动
    3. 需要特别注意的文化禁忌和行为规范
    4. 推荐可以体验当地文化的活动（如手工艺、传统表演等）
    输出格式：亲切友好的语气，突出趣味性和实用性。
    """
)
culture_chain = culture_prompt | llm | StrOutputParser()

context_chain = {
    "question": RunnablePassthrough(),
    "department": core_chain,
    "destination": RunnablePassthrough(),
    "days": RunnablePassthrough(),
    "budget": RunnablePassthrough(),
    "origin": RunnablePassthrough()
}

unknown_chain = (lambda x : "抱歉，我无法回答该问题。")

final_chain = context_chain | RunnableLambda(call_advisors)

if __name__ == "__main__":
    question = input("请输入目的地，旅行天数，预算等信息：")
    result = final_chain.invoke({"question": question})
    print(result)
    