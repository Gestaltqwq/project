import asyncio
import threading
from datetime import datetime
import time
async def asy_simulate(name):
    print(f"{name}开始思考")
    await asyncio.sleep(1)
    print(f"{name}思考完成")

def thr_simulate(name):
    print(f"{name}开始思考")
    time.sleep(1)
    print(f"{name}思考完成")

async def main():
    start = datetime.now().timestamp()
    await asyncio.gather(asy_simulate("模型1"),asy_simulate("模型2"),asy_simulate("模型3"),asy_simulate("模型4"),asy_simulate("模型5"))
    end = datetime.now().timestamp()
    cost = end - start
    return cost

if __name__ == "__main__":
    print("串行运行")
    start = datetime.now().timestamp()
    for i in range(5):
        thr_simulate(f"模型{i+1}")
    end = datetime.now().timestamp()
    cost = end - start
    print(f"串行耗时{round(cost,2)}秒")
    
    print("并行运行")
    threads = []
    start = datetime.now().timestamp()
    for i in range(5):
        tl = threading.Thread(target=thr_simulate,args=(f"模型{i+1}",))
        tl.start()
        threads.append(tl)
    for i in threads:
        i.join()
    end = datetime.now().timestamp()
    cost = end - start
    print(f"并行耗时{round(cost,2)}秒")

    print("异步运行")
    cost = asyncio.run(main())
    print(f"异步耗时{round(cost,2)}秒")
