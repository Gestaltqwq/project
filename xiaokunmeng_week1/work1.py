import asyncio
import time
async def greet(name,delay):
    await asyncio.sleep(delay)
    print(f"Hello,{name}!")
    return name

async def main():
    now = time.time()
    result = await asyncio.gather(greet("Alice",1),greet("Bob",2),greet("Carol",3))
    end = time.time()
    cost = end - now
    print(f"总共用了{round(cost,2)}秒")

asyncio.run(main())    