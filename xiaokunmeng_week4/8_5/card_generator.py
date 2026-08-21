from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os

class Card(BaseModel):
    name:str = Field(description="姓名")
    job:str = Field(description="职位")
    intro:str = Field(description="自我介绍")
    slogan:str = Field(description="个人slogan")
    skills:str = Field(description="技能列表")

load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")
llm = ChatOpenAI(model_name=model_name,api_key=api_key,base_url=base_url,temperature=0.3)


chat_prompt = ChatPromptTemplate.from_messages([
    ("system","你是一个专业的人力资源顾问，擅长帮人写简洁有力的自我介绍" ),
    ("human","请根据以下信息，帮我写一段 50 字以内的自我介绍。姓名：{name}，职位：{job}，技能：{skills}")
])
output_parser_1 = StrOutputParser()
chain = chat_prompt | llm | output_parser_1
char_result = chain.invoke({"name":"张三","job":"Python 开发工程师","skills":"Python, LangChain, FastAPI"})
print(char_result)
print(type(char_result))


prompt = PromptTemplate.from_template("""
    请根据以下信息，生成一句 15 字以内的个人 slogan，要求朗朗上口。姓名：{name}，职位：{job}
""")
response = prompt.format(name="张三",job="Python 研发工程师")
result = llm.invoke(response)
print(result.content)

output_parser_2 = JsonOutputParser(pydantic_object=Card)
messages = [
    SystemMessage(content=output_parser_2.get_format_instructions()),
    HumanMessage(content="请为以下人员生成名片数据:姓名：张三，职位：Python 研发工程师，技能：Python, LangChain, FastAPI")
]
response = llm.invoke(messages)
print(output_parser_2.parse(response.content))

print("\n" + "=" * 30)
print("      AI 智能名片")
print("=" * 30)
print(f"姓名：张三")
print(f"职位：Python 开发工程师")
print(f"自我介绍：{char_result}")
print(f"个人 slogan：{result.content}")
print(f"技能：Python, LangChain, FastAPI")
print("=" * 30)