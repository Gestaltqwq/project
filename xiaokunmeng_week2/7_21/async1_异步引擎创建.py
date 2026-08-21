"""
创建异步引擎步骤：引入异步引擎，引擎创建，会话创建
创建同步引擎步骤：引入同步引擎，引擎创建，会话创建（创建会话方式与异步不同）
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # 引入异步引擎
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine # 引入同步引擎
from datetime import datetime
import asyncio
from sqlalchemy import select
import random


#1. 引擎创建
#注意：驱动从pymysql改成aiomysql，协议也用mysql+变成mysql+aiomysql
engine1 = create_async_engine(
    "mysql+aiomysql://root:123456@localhost:3306/job_db?charset=utf8mb4",
    echo=True
    )#异步引擎
engine2 = create_engine(
    "mysql+pymysql://root:123456@localhost:3306/job_db?charset=utf8mb4",
    echo=True
)#同步引擎
# 异步会话工厂，需要指定class_=AsyncSession
AsyncSessionLocal = sessionmaker(
    engine1, class_=AsyncSession, expire_on_commit=False
)

SessionLocal = sessionmaker(bind=engine2)#同步会话
Base = declarative_base()#模型基类
# 2.定义模型
class JobPost(Base):
    __tablename__ = "job_post"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title = Column(String(100), nullable=False, comment="职位名称")
    company = Column(String(100), nullable=False, comment="公司名称")
    salary_min = Column(Float, default=0, comment="最低薪资(k)")
    salary_max = Column(Float, default=0, comment="最高薪资(k)")
    experience = Column(String(50), default="不限", comment="经验要求")
    jd_text = Column(Text, comment="职位描述原文")
    vector_id = Column(String(100), comment="关联向量ID")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<JobPost(self.titile)@{self.company}>"

# 3.异步建表
async def init_db():
    async with engine1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("数据表创建成功！")


# 4.异步插入数据（异步）
async def insert_job_async(title, company, salary_min, salary_max, experience, jd_text):
    # 插入单条岗位
    async with AsyncSessionLocal() as db:
        job = JobPost(
            title=title,
            company=company,
            salary_min=salary_min,
            salary_max=salary_max,
            experience=experience,
            jd_text=jd_text
        )
        db.add(job)
        await db.commit()
        await db.refresh(job) #刷新获取自增id
        print(f"插入成功：{job.title}，ID:{job.id}")
        return job.id
    
def insert_job(title, company, salary_min, salary_max, experience, jd_text):
    # 插入单条岗位
    with SessionLocal() as db:
        job = JobPost(
            title=title,
            company=company,
            salary_min=salary_min,
            salary_max=salary_max,
            experience=experience,
            jd_text=jd_text
        )
        db.add(job)
        db.commit()
        db.refresh(job) #刷新获取自增id
        print(f"插入成功：{job.title}，ID:{job.id}")
        return job.id


# 5.异步查询数据
async def query_jobs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(JobPost))
        jobs = result.scalars().all()
        print(f"共{len(jobs)}条数据")
        for job in jobs:
            print(job)
        return jobs

def get_job_list(count):
    job = []
    companies = ["字节跳动", "百度", "腾讯", "京东", "美团", "阿里"]
    experiences = ["不限", "1-3年", "3-5年", "5年以上"]
    titles = ["Python开发", "Java开发", "前端开发", "算法工程师", "测试开发", "产品经理"]
    jd_texts = [
        "负责Python项目的开发，包括后端、前端、数据库等。",
        "负责核心交易系统，精通Java、Spring Cloud、MySQL...",
        "负责Web端产品开发，熟悉Vue3、TypeScript...",
        "负责NLP算法研发，熟悉Transformer、BERT...",
        "负责自动化测试框架搭建，熟悉Python、Selenium...",
        "负责产品需求分析，熟悉产品需求文档..."
    ]
    salary_min = [15, 20, 25, 30, 35, 40]
    salary_max = [20, 25, 30, 35, 40, 45]
    for i in range(count):
        random_num = random.randint(0, 5)
        job.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "salary_min": salary_min[random_num],
            "salary_max": salary_max[random_num],
            "experience": random.choice(experiences),
            "jd_text": random.choice(jd_texts)
        })
    return job
#================主函数=================
async def main():
    #1. 建表
    #await init_db()

    # #2. 插入示例数据
    # await insert_job(
    #     title="Python开发",
    #     company="字节跳动",
    #     salary_min=15,
    #     salary_max=20,
    #     experience="3年以上",
    #     jd_text="负责Python项目的开发，包括后端、前端、数据库等。"
    # )
    # await insert_job(
    #     "Java高级工程师", "阿里巴巴", 20, 40,
    #     "5年以上", "负责核心交易系统，精通Java、Spring Cloud、MySQL..."
    # )
    # await insert_job(
    #     "前端开发工程师", "腾讯", 12, 25,
    #     "1-3年", "负责Web端产品开发，熟悉Vue3、TypeScript..."
    # )
    # await insert_job(
    #     "算法工程师", "百度", 25, 50,
    #     "3-5年", "负责NLP算法研发，熟悉Transformer、BERT..."
    # )
    # await insert_job(
    #     "测试开发工程师", "美团", 10, 20,
    #     "不限", "负责自动化测试框架搭建，熟悉Python、Selenium..."
    # )
    start = datetime.now().timestamp()
    job_list = get_job_list(1000)
    batch_size = 10
    for i in range(0, len(job_list), batch_size):
        batch = job_list[i:i+batch_size]
        tasks = [insert_job_async(**job) for job in batch]
        await asyncio.gather(*tasks)
    cost1 = datetime.now().timestamp() - start
    

    start = datetime.now().timestamp()  
    for job in job_list:
        insert_job(
            job["title"], job["company"], job["salary_min"], job["salary_max"],
            job["experience"], job["jd_text"]
        )
    cost2 = datetime.now().timestamp() - start
    print(f"异步耗时：{cost1}秒")
    print(f"耗时：{cost2}秒")
    

    # 3. 查询数据
    #print("\n查询所有岗位数据==========")
    #await query_jobs()
    
    # 4. 关闭引擎连接 （避免Event loop is closed)
    await engine1.dispose()
    engine2.dispose()
    print("数据库引擎已关闭")


if __name__ == "__main__":
    asyncio.run(main())




