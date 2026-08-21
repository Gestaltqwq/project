import time
from datetime import datetime
import threading
import asyncio

lock = threading.Lock()

class AIModel():
    def __init__(self,name,model_type):
        self.name = name
        self.model_type = model_type
    
    async def predict(self,input_data):
        raise NotImplementedError("该子类未实现该方法")
    
class TextModel(AIModel):
    def __init__(self,name,model_type):
        super().__init__(name,model_type)

    async def predict(self,input_data):
        print(f"文本模型{self.name}正在生成文本...")
        await asyncio.sleep(1)
        return f"文本结果：{input_data}"

class ImageModel(AIModel):
    def __init__(self,name,model_type):
        super().__init__(name,model_type)

    async def predict(self,input_data):
        print(f"图像模型{self.name}正在识别图像...")
        await asyncio.sleep(2)
        return f"图像结果：{input_data}"

async def user_request(user_name,model,input_data):
    record_dict = {}
    start = datetime.now()
    result = await model.predict(input_data)
    end = datetime.now()
    cost = int(end.timestamp() - start.timestamp())
    record_dict['user'] = user_name
    record_dict['model名'] = model.name
    record_dict['cost'] = cost
    record_dict['result'] = result
    return record_dict
    
async def main():
    text_model = TextModel("text_model","text")
    image_model = ImageModel("image_model","image")
    start = datetime.now().timestamp()
    result = await asyncio.gather(
        user_request("用户1",text_model,"数据"),
        user_request("用户2",text_model,"数据"),
        user_request("用户3",image_model,"数据"),
        user_request("用户4",image_model,"数据")
        )
    end = datetime.now().timestamp()
    cost = end - start
    for i in result:
        print(i)
    return cost

cost = asyncio.run(main())
print(f"总共用{round(cost,2)}秒")


