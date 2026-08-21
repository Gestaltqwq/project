"""请求校验：模型模块"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    """训练请求：models 指定算法、params 自定义超参、test_size/random_state 控制划分"""
    models: Optional[List[str]] = Field(default=None, description="要训练的算法列表，空则全部")
    params: Optional[Dict[str, Dict]] = Field(default=None, description="算法超参")
    test_size: float = Field(default=0.2, gt=0.0, lt=1.0, description="测试集比例")
    random_state: int = Field(default=42, description="随机种子")
