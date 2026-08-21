"""请求校验：邮件模块"""
from typing import Optional, List
from pydantic import BaseModel, Field


class GenerateEmailRequest(BaseModel):
    """批量生成邮件：limit=取 top N；customer_ids=指定客户"""
    limit: Optional[int] = Field(default=None, ge=1, le=100, description="取 top N 高潜客户")
    customer_ids: Optional[List[int]] = Field(default=None, description="指定客户 ID 列表")


class PromptUpdateRequest(BaseModel):
    """更新 Prompt 模板"""
    content: str = Field(..., min_length=1, description="模板内容")


class EmailUpdateRequest(BaseModel):
    """更新邮件内容"""
    email_subject: Optional[str] = Field(default=None, description="标题")
    email_content: Optional[str] = Field(default=None, description="正文")


class EmailStatusRequest(BaseModel):
    """标记邮件状态"""
    status: str = Field(..., description="generated/edited/sent/failed")


class BatchDeleteRequest(BaseModel):
    """批量删除邮件"""
    record_ids: List[int] = Field(..., min_length=1, description="记录 ID 列表")
